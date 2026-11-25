# Anatomy project: revision B

Use the `anatomy` skill for all work in this folder, and follow its references/design-revisions.md.

This folder is revision B of `../this-is-my-version-of-a` ("This is my version of a GPU Server Super Compuer, redesign
from this concept"), copied from it on 2026-11-24. Never write to `../this-is-my-version-of-a` or any other project
folder: it is a completed version and must stay exactly as it is.

The user's revision request is in inputs/revision-request.md. What changed is in REV-B.md.

Layout:
- `anatomy-tstack-gpu-tower/prototype/` is the rev B engineering package (64 GPUs, 16 per column): CAD, drawings,
  KiCad boards, harness, thermal-fluid calc, BOM. Rebuild scripts are inside it (see REV-B.md).
- `anatomy-tstack-gpu-tower/sim-rev-b/` is the rev B digital twin (`node server.mjs`, tests `node run-tests.mjs`).
- The rev A blueprint documents (00-overview.md .. 90-rebuild-spec.md), `software/` and `build/` are carried over from
  rev A unchanged and still describe the 8-node / 32-GPU tower. They are superseded by REV-B.md where they differ.
