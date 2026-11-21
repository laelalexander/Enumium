# Industrial design and visual fidelity

The 3D model is the first thing the user judges. A product made of square blocks, faceted cylinders and flat grey
colours reads as a placeholder even when the engineering behind it is right. The user's bar (2026-11-21): **nothing
square without curves and styling; the model should look like a true-to-life working product.** This file is
mandatory for every physical product, alongside `hardware-engineering.md` and `drawings.md`.

## 1. No raw boxes

Every BUILD part ends as a manufacturable, styled shape. A `Box()` or bare `Cylinder()` is a starting block, never the
finished part.

| Part type | Minimum treatment |
|---|---|
| Machined / printed blocks, brackets, housings | Fillet every outside edge (R ≥ 1.5 mm small parts, R ≥ 3 mm hand-sized, R ≥ 8–15 mm parts over 300 mm). Inside corners get tool-radius fillets (R ≥ tool/2). Chamfer 0.5–1 × 45° where a fillet would weaken a seat. Lightening pockets with ribs where the load allows. |
| Sheet metal | Real bend radii (≥ 1 × t), reliefs, hemmed or broken edges; no knife-sharp flats. |
| Composite and moulded shells, covers, fairings, bodies | Lofted or swept surfaces through real sections (superellipses, aerofoils, splines), G2-continuous where visible, draft ≥ 1–2° for the mould, a defined shut-line gap (2–4 mm) and a lip/return flange where panels meet. |
| Ducts, inlets, nozzles | Bell-mouth / rounded inlet lip (lip radius ≥ 6–10 % of the diameter), tapered exit, faired struts and stator vanes with aerofoil sections. |
| Wings, rails, beams that are seen | Aerofoil or rounded-rectangle sections, tapered tips with end caps, faired joints (no butt joints between flat faces). |
| Rotors, fans, propellers | Twisted, tapered blades with an aerofoil section and a spinner; never flat paddles. |
| Tubes, frames | Real tube (OD/wall), mitred/coped joints with weld fillets shown, end caps. |

Check it with the script in §6. A part still flagged boxy needs a reason in `parts.json` `note` (for example
"stock flat bar, edges broken 0.5 mm").

## 2. Bought parts are modelled as the real thing

A BUY part is the manufacturer's actual shape, not an envelope box:

1. Use the manufacturer's STEP when it can be downloaded (McMaster, Misumi, SKF, Harmonic Drive, motor makers), saved
   under `prototype/mechanical/vendor/` with its source URL in `parts_meta`/`parts.json`.
2. Otherwise model it from the datasheet drawing to the level a photo would show: motors with their stator can, cooling
   fins, shaft, flange bolt circle and connector block; bearings with races, seals and chamfers; electronics boxes with
   rounded extrusion bodies, heat-sink fins, connectors, mounting ears and labels; fasteners with real heads (hex, socket,
   Torx), washers and thread length.
3. Record `geometry: "vendor STEP" | "datasheet model" | "envelope"` per part in `parts.json`. `envelope` is only for
   something truly unknown, and it is listed as an open item.

## 3. Materials and finishes travel with the model

- In `assembly.json`, give each part a `material` from this list so the Design Studio, the viewer and Blender show it
  right: `Painted body, gloss`, `Painted body, satin`, `Carbon fibre (CFRP)`, `Aluminium, machined`,
  `Aluminium, anodised black`, `Titanium (LPBF / machined)`, `Steel, zinc plated`, `Stainless steel`,
  `Steel, powder coated`, `Copper`, `Brass`, `Printed plastic (PETG/PLA)`, `Moulded plastic`, `Rubber`,
  `Glass / polycarbonate`, `Smoked polycarbonate`, `PCB (green solder mask)`, `Motor / electronics, dark`,
  `Battery / pack wrap`, `Composite tank (white)`, `Foam / insulation`, `Wood`. Add `color` ("#rrggbb") for paint
  and anodise colours.
- Write a GLB beside the STLs (`assembled/<product>.glb`) with PBR materials (metalness/roughness, clearcoat for paint
  and CFRP, transmission for glass) and one named node per part.
- Choose a livery: a body colour, an accent colour and where each goes. Record it in the blueprint.

## 4. Smooth tessellation

Faceted cylinders make a good model look cheap. Export meshes with tight tolerances:

- build123d: `export_stl(shape, path, tolerance=0.02, angular_tolerance=0.1)` for parts up to ~300 mm; scale the
  linear tolerance with size (≈ size/5000) for big parts, angular tolerance ≤ 0.15 rad always.
- CadQuery: `exporters.export(shape, path, tolerance=0.02, angularTolerance=0.1)`.
- Check: no visible facets on any round edge in the renders (§5); the Design Studio's "Lines" look makes facets obvious.

## 5. Renders that sell the design

Every product ends with photoreal renders in `prototype/renders/`: a hero three-quarter view, front, side, top, an
exploded view and a detail close-up of the most interesting mechanism. Render with Blender headless (`blender -b`,
Cycles, GPU when present, denoised, AgX view transform, shadow-catcher floor, three-point area lights), or use the
Anatomy app's bridge script `app/blender/anatomy_blender.py` with a GLB of the assembly. Look at every render before
presenting it; a render that shows a box where a part should be is a defect to fix, not a picture to ship.

## 6. Self-check (run before you call the model done)

For each STL in the assembly: compute triangle count and fill ratio (mesh volume ÷ bounding-box volume).

- fill > 0.93 and fewer than ~140 triangles: a plain block. Restyle it (§1/§2) or give a reason.
- fewer than ~300 triangles on a part larger than 40 mm: a low-detail stand-in. Re-model or re-export (§4).

Report the count of flagged parts in the hand-off summary; the target is zero. The Design Studio shows the same flags
(▢) so the user sees them too.
