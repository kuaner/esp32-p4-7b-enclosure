"""Assembly fit reference corrected only for user-confirmed outward flex bends.

The vendor files remain untouched. The rigid glass, LCD housing, board and all
components are retained. This does not predict the actual folded flex routing.
"""
from pathlib import Path
import json
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]
REF=ROOT/'design/reference'
SHIFT=(-82,-47.5,8.8)

def component(idx):
    return cq.Shape.importBrep(str(REF/f'part_{idx:04d}.brep')).translate(SHIFT)

def assembled_screen_component(idx):
    s=component(idx)
    if idx not in [1337,1338]:
        return s
    # Below LCD metal's lower edge (Y=-47.55), behind the glass back (Z=1.9).
    # These localized regions contain only modeled flex, no rigid screen body.
    xa,xb=(-74,-54) if idx==1337 else (-15,16)
    cutter=cq.Solid.makeBox(xb-xa,12.45,15,cq.Vector(xa,-60,1.90001))
    s=s.cut(cutter)
    if idx==1337:
        # The touch-flex bend also extends past the glass edge at shallower Z.
        # Keep the entire rigid lens (minimum Y=-49.085) at every depth.
        outside_glass=cq.Solid.makeBox(20,10.915,17,cq.Vector(-74,-60,-1))
        s=s.cut(outside_glass)
    return s

def assembly_fit_reference():
    rows=json.loads((REF/'components.json').read_text())
    return cq.Compound.makeCompound([assembled_screen_component(row['id']) for row in rows])

def reference_notes():
    return {
        'basis':'User confirmed the assembled screen edge is flat; no outward flex clearance is needed.',
        'unchanged':'All rigid glass/LCD/PCB parts, original mounts and electronic components.',
        'flex_only_exclusion':'Parts 1337/1338: Y < -47.55, Z > 1.90001, X [-74,-54] / [-15,16]. Part 1337 also Y < -49.085, X [-74,-54].',
        'limitation':'Outward flex bends are excluded from rigid-fit checks; folded cable shape is not simulated.',
        'drawing_glass_nominal_mm':[164.28,99.74,1.9],
        'step_glass_front_outline_mm':[164.28,99.17],
        'glass_centre_y_mm':0.5,
    }
