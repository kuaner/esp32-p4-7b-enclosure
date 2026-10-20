# Project instructions

## Scope and source of truth

This is a mechanical CAD project for Waveshare ESP32-P4-WIFI6-Touch-LCD-7B. Work in millimetres. Communicate with the maintainer in Chinese unless asked otherwise. Read `README.md`, `output/current/README.md` and `docs/DEVELOPMENT.md` before changing geometry.

Editable source is `cad/`; `output/current/` is the sole current deliverable. Update existing files in place. Do not add numbered model generations, parallel design folders, backup models or multiple archives. Git history records past changes. Preserve local manufacturer files unchanged.

`parameters.json` records dimensions, but several features are defined directly in Python. Inspect the geometry before assuming that editing JSON changes the model. Preview images must be rendered from actual solids; concept illustrations cannot establish fit or printability.

## Accepted constraints

- Three printed pieces: one screen shell, one speaker pod, one stand. Each is a single solid. Do not split the stand upright from its flat plinth.
- Main shell: sides and rear integrated, open front, stepped flush glass seat. No separate front bezel. The flex edge stays straight; do not add width for the outward-bent flex in the vendor STEP.
- Screen installation: switch/USB (+X) side first at an angle, then button (-X) side. Original four M2.5 × 8 mm screws, no insert nuts or extra fastener system.
- Keep power, switch, buttons, TF access and both full microphone rays clear. Camera accommodation is only the centred 22 × 4 mm top ribbon opening.
- Speaker nominal: 99.5 × 44.5 × 20.8 mm; maximum 100 × 45 × 21.1 mm. Open pod with outward grille, frame supports and simple internal clips, no separate lid. Optional thin tape touches the frame only.
- Speaker lead passes through the centred shell opening and is concealed by the mounted pod. No ties or unnecessary side openings.
- Expansion interface: gravity hooks, 8 mm travel, 125 mm horizontal pitch. Upper row hangs modules downward; lower row is reversed so the screen moves downward onto a fixed base. No independent latch, sliding key, pin or anti-lift lock.
- Installed stand must cover complete lower mounting apertures, including the existing 1 mm coverage-margin checks, and leave the full microphone rays clear.
- Stand: one-piece diamond upright with a flat rounded rectangular plinth. No large central triangle, X-shaped tabletop footprint or added waterdrop holes.
- Preserve support-free print orientations. Avoid new suspended islands, long bridges or abrupt cantilevers. Do not add parts solely to make printing possible. Disabling slicer supports alone does not prove support-free geometry.

These describe the accepted design; later explicit user instructions can change them.

## Files and coordinates

`build_design.py` builds the shell and pod and exports all models. `stand.py` defines the stand and transforms. `interface.py` defines receivers, hooks and the blank adapter. `fit_reference.py` defines the vendor frame shift and localized user-confirmed flex exclusions. `verify_design.py` checks discrete CAD assembly positions. `check_printability.py` audits module layers. `check_slice.py` performs optional real Bambu slicing in an isolated temporary configuration. `render_design.py` renders actual CAD. `package_design.py` and `check_release.py` package and validate the release.

Engineering coordinates use +Y up and +Z toward the rear. STEP uses assembly coordinates; STL uses printing coordinates with minimum Z at zero. Use the existing transforms; do not hand-position previews or change only one export.

## Verification

Use Python 3.12 in a virtual environment with `cad/requirements.txt`. Basic construction needs no manufacturer reference:

```sh
python cad/build_design.py
python cad/check_printability.py
```

Geometry changes affecting the assembled device also require the exact manufacturer reference described in `docs/DEVELOPMENT.md`, then:

```sh
python cad/analyze_board.py
python cad/verify_design.py
python cad/check_slice.py
python cad/render_design.py
python cad/package_design.py --manifest-only
python cad/check_release.py
```

Bambu checks require the documented macOS app/profile; never overwrite user settings. Rendering needs a CJK font and VTK/OpenGL. If an optional dependency or vendor file is unavailable, report the missing check. Do not fabricate passes, attach old success reports to new geometry or relax checks to force a release.

Require valid single solids and watertight connected meshes for all three parts. Preserve gravity seating, pull-out blocking, acoustic clearance, hidden wiring, aperture coverage and installation motions. Fit checks sample discrete positions; do not claim continuous sweep or strength simulation.

After geometry changes regenerate affected STL, STEP, previews and evidence together. Changed STL requires new slice evidence. Do not describe CAD, layer audits or slicing as physical validation. Current design has not been physically prototyped. Local work refreshes the manifest only; the GitHub release workflow creates ZIPs and uploads model assets after checks pass. See the release procedure in `docs/DEVELOPMENT.md`.

## Publication hygiene

Original code, models and documentation use MIT. Follow `THIRD_PARTY_NOTICES.md`: do not publish vendor STEP/DWG/PDF, BREP cache, the speaker reference image, environment files, credentials, personal absolute paths or machine-specific G-code. Respect `.gitignore` and the packaging allowlist. Preserve original third-party files locally.

Use relative repository links. Keep download links, archive contents and hashes consistent. Publication and messaging actions require the user's authorization; this file grants no standing permission to publish future changes.
