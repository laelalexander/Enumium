"""Anatomy Design Studio <-> Blender bridge.

Started by the Anatomy app (design.js), never by hand:
  blender [-b --factory-startup] --python anatomy_blender.py -- <scene.glb> <open|render> <out.png> <return.json>
          <sculpt_dir> <samples> <width> <height> <scene.blend>

scene.glb is the edited model exported by the design editor: one node per part, Z up, metres, each node's origin at
the part's centre, custom properties anatomy_file / anatomy_name / anatomy_material.

render: builds a studio (shadow-catcher floor, key/fill/rim area lights, soft world), frames the product and renders
        a photoreal Cycles image to out.png (GPU when there is one), then quits.
open:   the same studio in the Blender window for the user to sculpt, restyle and render by hand. Every save
        (Ctrl+S) writes return.json (each part's placement) and, for parts whose mesh was changed, a binary STL in
        sculpt_dir (part-local frame, mm). The design editor reads both with "Bring back from Blender".
"""
import bpy, sys, os, json, math, struct, hashlib
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
GLB, MODE, OUT, RET, SCULPT = argv[0], argv[1], argv[2], argv[3], argv[4]
SAMPLES, W, H = int(argv[5]), int(argv[6]), int(argv[7])
BLEND = argv[8] if len(argv) > 8 else ""


def log(*a):
    print("[anatomy]", *a, flush=True)


def mesh_hash(ob):
    me = ob.data
    h = hashlib.sha1()
    h.update(struct.pack("<II", len(me.vertices), len(me.polygons)))
    co = [0.0] * (len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    h.update(struct.pack("<%dd" % min(len(co), 30000), *[round(c, 6) for c in co[:30000]]))
    return h.hexdigest()


def part_objects():
    return [o for o in bpy.data.objects if o.type == "MESH" and o.get("anatomy_file")]


# ---------------------------------------------------------------- scene
def build_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.ops.import_scene.gltf(filepath=GLB)
    parts = []
    for ob in list(bpy.data.objects):  # list(): renaming reorders bpy.data.objects
        if ob.type != "MESH":
            continue
        # The exporter puts the part's metadata in glTF extras, which arrive as custom properties on the object
        # (or on its parent empty when the importer adds one).
        src = ob if ob.get("anatomy_file") else (ob.parent if ob.parent and ob.parent.get("anatomy_file") else None)
        if src is not None and src is not ob:
            for k in ("anatomy_file", "anatomy_name", "anatomy_material"):
                if k in src:
                    ob[k] = src[k]
        if ob.get("anatomy_file"):
            ob["anatomy_hash"] = mesh_hash(ob)
            ob.name = str(ob.get("anatomy_name") or ob["anatomy_file"])[:60]
            parts.append(ob)
    # bounds of the product
    lo = Vector((1e9, 1e9, 1e9)); hi = Vector((-1e9, -1e9, -1e9))
    for ob in parts:
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    if not parts:
        lo, hi = Vector((-1, -1, 0)), Vector((1, 1, 1))
    size = hi - lo
    R = max(size.x, size.y, size.z)
    ctr = (lo + hi) / 2

    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"; sc.unit_settings.length_unit = "MILLIMETERS"
    sc.render.engine = "CYCLES"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
            try:
                prefs.compute_device_type = kind
                prefs.get_devices()
                devs = [d for d in prefs.devices if d.type == kind]
                if devs:
                    for d in prefs.devices:
                        d.use = d.type == kind
                    sc.cycles.device = "GPU"
                    log("rendering on", kind)
                    break
            except Exception:
                continue
    except Exception as e:
        log("GPU setup skipped:", e)
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        try:
            sc.view_settings.view_transform = "Filmic"
        except Exception:
            pass
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.film_transparent = False

    # world: soft studio grey with a gentle gradient
    world = bpy.data.worlds.new("Anatomy studio") if not sc.world else sc.world
    sc.world = world
    world.use_nodes = True
    nt = world.node_tree; nt.nodes.clear()
    bg = nt.nodes.new("ShaderNodeBackground"); out = nt.nodes.new("ShaderNodeOutputWorld")
    grad = nt.nodes.new("ShaderNodeTexGradient"); ramp = nt.nodes.new("ShaderNodeValToRGB"); tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, -math.pi / 2, 0)
    ramp.color_ramp.elements[0].color = (0.62, 0.64, 0.68, 1); ramp.color_ramp.elements[1].color = (0.93, 0.94, 0.96, 1)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Color"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.35
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    # shadow-catcher floor + a large white cyclorama behind
    bpy.ops.mesh.primitive_plane_add(size=R * 12, location=(ctr.x, ctr.y, lo.z))
    floor = bpy.context.active_object; floor.name = "Studio floor"; floor.is_shadow_catcher = True

    def area(name, loc, energy, size, color=(1, 1, 1)):
        d = bpy.data.lights.new(name, "AREA"); d.energy = energy; d.size = size; d.color = color
        o = bpy.data.objects.new(name, d); bpy.context.collection.objects.link(o)
        o.location = loc
        direction = ctr - Vector(loc); o.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        return o
    k = (R / 1.0) ** 2  # light energy scales with the square of the distance
    area("Key", ctr + Vector((-1.2 * R, -1.4 * R, 1.6 * R)), 160 * k, R * 1.2, (1.0, 0.97, 0.92))
    area("Fill", ctr + Vector((1.6 * R, -0.8 * R, 0.8 * R)), 60 * k, R * 1.6, (0.9, 0.95, 1.0))
    area("Rim", ctr + Vector((0.4 * R, 1.8 * R, 1.2 * R)), 160 * k, R * 0.9)
    area("Top", ctr + Vector((0, 0, 2.2 * R)), 50 * k, R * 2.0)

    cam_d = bpy.data.cameras.new("Camera"); cam_d.lens = 50
    cam = bpy.data.objects.new("Camera", cam_d); bpy.context.collection.objects.link(cam)
    cam.location = ctr + Vector((1.25 * R, -1.55 * R, 0.85 * R))
    cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam_d.clip_start = R / 1000; cam_d.clip_end = R * 100
    sc.camera = cam
    # fit the product in frame
    bpy.ops.object.select_all(action="DESELECT")
    for ob in parts:
        ob.select_set(True)
    try:
        bpy.context.view_layer.update()
        bpy.ops.view3d.camera_to_view_selected() if bpy.context.area and bpy.context.area.type == "VIEW_3D" else None
    except Exception:
        pass
    # keep a little margin: pull the camera back 8 %
    cam.location = ctr + (cam.location - ctr) * 1.08
    cam_d.dof.use_dof = False
    log("scene ready:", len(parts), "parts, size", tuple(round(v, 3) for v in size), "m")
    return parts


# ---------------------------------------------------------------- return trip (save hook)
def write_stl(path, ob):
    me = ob.data
    me.calc_loop_triangles()
    co = [v.co for v in me.vertices]
    with open(path, "wb") as f:
        f.write(b"anatomy sculpt".ljust(80, b" "))
        f.write(struct.pack("<I", len(me.loop_triangles)))
        for t in me.loop_triangles:
            a, b, c = (co[i] * 1000.0 for i in t.vertices)  # part-local frame, m -> mm
            n = t.normal
            f.write(struct.pack("<12fH", n.x, n.y, n.z, a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z, 0))


@bpy.app.handlers.persistent
def on_save(*_):
    try:
        os.makedirs(SCULPT, exist_ok=True)
        out = {"saved": bpy.data.filepath, "parts": {}}
        for ob in part_objects():
            loc, rot, scl = ob.matrix_world.decompose()
            rec = {"name": ob.name, "position": [loc.x * 1000, loc.y * 1000, loc.z * 1000],
                   "quaternion": [rot.x, rot.y, rot.z, rot.w], "scale": [scl.x, scl.y, scl.z], "hidden": ob.hide_get() or ob.hide_render}
            if mesh_hash(ob) != ob.get("anatomy_hash"):
                name = os.path.splitext(os.path.basename(str(ob["anatomy_file"])))[0] + ".stl"
                write_stl(os.path.join(SCULPT, name), ob)
                rec["mesh"] = name
            mat = ob.active_material
            if mat is not None and mat.use_nodes:
                p = mat.node_tree.nodes.get("Principled BSDF")
                if p is not None:
                    c = p.inputs["Base Color"].default_value
                    srgb = lambda v: 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
                    rec["color_linear"] = [max(0.0, min(1.0, v)) for v in c[:3]]
                    rec["color"] = "#%02x%02x%02x" % tuple(round(srgb(v) * 255) for v in rec["color_linear"])
                    rec["metalness"] = p.inputs["Metallic"].default_value
                    rec["roughness"] = p.inputs["Roughness"].default_value
            out["parts"][str(ob["anatomy_file"])] = rec
        with open(RET, "w") as f:
            json.dump(out, f, indent=1)
        log("wrote", RET)
    except Exception as e:
        log("save hook failed:", e)


parts = build_scene()
if MODE == "render":
    bpy.context.scene.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    log("rendered", OUT)
    sys.exit(0)
else:
    if BLEND:
        try:
            bpy.ops.wm.save_as_mainfile(filepath=BLEND)
        except Exception as e:
            log("could not save", BLEND, e)
    bpy.app.handlers.save_post.append(on_save)
    log("ready: sculpt or restyle, then Ctrl+S to send the changes back to Anatomy")
