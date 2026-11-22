# Design revisions from the Design Studio

The Anatomy app has a 3D **Design Studio** (`app/public/editor.html`). The user selects parts, moves, rotates and
scales them, changes dimensions from the parameter file, picks materials and colours, ticks styling options, writes
notes, and can sculpt in Blender. **Rebuild as new revision** then:

1. copies the project into a new folder `<project>-rev-<letter>` (sources, models, drawings, docs; no venvs, caches
   or run logs), marked in `.anatomy/project.json` with `revisionOf`, `revisionRoot` and `revision`;
2. writes the edits to `inputs/design-edits.md` (readable), `inputs/design-edits.json` (exact values),
   `inputs/design-edits.png` (picture of the edited model) and `inputs/sculpt/*.stl` (shapes sculpted in Blender);
3. starts a run in the new folder that follows this file.

The completed version (`../<project>`) is never changed. Do not write there. Running its tools read-only (its `.venv`
Python, `.tools`) is fine.

## The edits file

```json
{
  "units": "mm", "up": "Z",
  "params": { "FAN_D": { "file": "…/hx1_params.py", "from": 1050, "to": 1100 } },
  "parts": {
    "FL_duct_shell.stl": {
      "name": "Duct shell (front left duct)", "line": "DU-01",
      "center": [x, y, z], "size": [dx, dy, dz],          // the part's bounding box before the edit
      "translate": [dx, dy, dz],                            // mm, world axes
      "rotate": [rx, ry, rz],                               // deg, XYZ order, about "center"
      "scale": [sx, sy, sz],                                // about "center"
      "material": "Carbon fibre (CFRP)", "color": "#c8102e",
      "styles": ["Rounded intake lip / bell-mouth", …],
      "note": "free text from the user",
      "mesh": "inputs/sculpt/FL_duct_shell.stl",            // sculpted target shape, part-local frame, mm
      "removed": true
    }
  },
  "global": { "style": "Aerospace (…)", "detail": "Showroom", "autoStyle": true, "notes": "…" }
}
```

## How to apply them

Work through them in this order, and keep a table in `prototype/REVISION-<letter>.md` with one row per edit:
what was asked, what you changed (file and function or parameter), and how you checked it.

1. **Parameters.** Change the values in the parameter file. Everything else derives from it, so rebuild the model
   and run the mechanism/interference check. If a change breaks a requirement (clearance, strength, mass, fit
   on the print bed), make the smallest compensating change and record it; do not silently drop the edit.
2. **Moves, rotations, scales.** These are design intent, not mesh transforms. Translate them into the parametric
   source: move the part's datum/parameters, change the driving dimensions for a scale, re-mate whatever it
   connects to (brackets, fasteners, wiring lengths, harness routes). Mirror an edit onto a symmetric twin only
   when the user edited both or wrote so in a note; otherwise ask yourself whether symmetry is a requirement and
   record the choice.
3. **Removed parts.** Remove from the CAD, BOM, drawings, G-code and assembly steps; fix what depended on them.
4. **Swaps and notes.** A note like "swap for a smaller motor" is a real redesign: pick a real part (BUY rules in
   `parts-and-bom.md`), update the BOM with qty traced to the design, and log it as an ECO with the reason.
5. **Styling.** Apply every `styles` entry and the `global` direction using `industrial-design.md`. With
   `autoStyle: true`, also restyle every part that the §6 self-check flags as boxy or low-detail, not only the
   ones the user touched. `detail: "Showroom"` means §1–§4 of that file for every visible part.
6. **Sculpted meshes.** A `mesh` is the target shape, drawn by hand. Rebuild it as real CAD (lofts, sweeps,
   fillets) that matches it within a few mm, then delete nothing from `inputs/`. Do not ship the mesh as the part.
7. **Materials and colours.** Change the material in `parts_meta`/`parts.json`, the BOM `key_spec`, the drawing
   title-block material note and, if the process changes (printed → machined, aluminium → CFRP), the routing
   (print list, Xometry, cut files). Put `material` and `color` on each part in `assembly.json`.

## Regenerate everything that depends on the geometry

STEP and STL exports (tight tessellation), `assembly.json` + `parts.json` + the GLB, drawings and DXF cut files
(mm and inch), BOM and its checks, G-code for every printed part (re-slice and re-check), the illustrated assembly
guide, `build/build.json`, the simulator's parameters, and photoreal renders. Then look at the renders next to
`inputs/design-edits.png`: every requested change must be visible.

Update `anatomy.json` (title with "rev <letter>") and the blueprint's overview with a short "Changes from
rev <previous>" section. In the hand-off summary list every edit as done, changed (with why) or not done (with why).
