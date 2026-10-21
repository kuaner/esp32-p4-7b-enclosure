"""Unmodified manufacturer geometry, including both FPC loops.

Physical feedback requires local shell reliefs. No flex geometry is excluded.
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
    return component(idx)

def assembly_fit_reference():
    rows=json.loads((REF/'components.json').read_text())
    return cq.Compound.makeCompound([assembled_screen_component(row['id']) for row in rows])

def reference_notes():
    return {
        'basis':'Prototype feedback: smaller STEP glass profiles and two local FPC reliefs are required.',
        'unchanged':'All original components and complete FPC loops retained; no geometry exclusions.',
        'flex_only_exclusion':None,
        'limitation':'Vendor FPC pose is checked, not cable strain or arbitrary folded routes.',
        'drawing_glass_nominal_mm':[164.28,99.74,1.9],
        'step_glass_front_outline_mm':[164.28,99.17],
        'step_glass_rear_outline_mm':[163.88,98.77],
        'glass_centre_y_mm':0.5,
    }
