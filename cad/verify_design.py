"""Discrete mechanical assembly checks for the gravity mounts, not strength proof."""
from pathlib import Path
import json, math
import cadquery as cq
from fit_reference import assembled_screen_component,reference_notes
from primitives import box,rr
from interface import SPEC,receiver,flat_adapter as tile
from wire_route import (wire_envelope,board_wire_envelope,board_plug_envelope,
                        BOARD_PLUG_XY,PLUG_WALL_LAND)
from screen_geometry import glass_envelope
from evidence import hashes,model_sources,stl_inputs

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/current/verification'
read=lambda n:cq.Shape.importBrep(str(OUT/f'{n}.brep'))
body=read('shell');pod=read('speaker');stand=read('stand')
checks={}
def check(name,a,b):
    ab=a.BoundingBox();bb=b.BoundingBox()
    disjoint=any([ab.xmax<bb.xmin,bb.xmax<ab.xmin,ab.ymax<bb.ymin,
                  bb.ymax<ab.ymin,ab.zmax<bb.zmin,bb.zmax<ab.zmin])
    if disjoint:
        v=0.0
    elif b is board:
        # Exact intersection with the assembly AABB first often proves that
        # a rear module is wholly outside the electronics, without 1339 booleans.
        clipped=a.intersect(box(bb.xlen,bb.ylen,bb.zlen,(bb.xmin+bb.xmax)/2,
                                (bb.ymin+bb.ymax)/2,bb.zmin))
        v=clipped.intersect(b).Volume() if clipped.Solids() else 0.0
    else:
        v=a.intersect(b).Volume()
    checks[name]={'intersection_mm3':round(v,7),'pass':v<.001}
    print(name,checks[name],flush=True)

# A 1 mm expanded aperture projection must be covered by solid stand material.
for x in [-62.5,62.5]:
    expanded=rr(12,11,1.8,22.3,1,x,-36).fuse(box(6.8,18.7,1,x,-32.15,22.3))
    v=expanded.cut(stand).Volume()
    checks[f'lower_aperture_{x}_covered_with_1mm_margin']={'uncovered_mm3':round(v,7),'pass':v<.001}
    print('Mount cover',x,checks[f'lower_aperture_{x}_covered_with_1mm_margin'],flush=True)

print('Load assembled screen reference',flush=True)
expected=json.loads((ROOT/'cad/vendor_reference.json').read_text())
source=json.loads((ROOT/'design/reference/source.json').read_text())
assert source['sha256']==expected['sha256'] and source['components']==expected['components'], 'Rebuild vendor cache'
rows=json.loads((ROOT/'design/reference/components.json').read_text())
components=[assembled_screen_component(row['id']) for row in rows]
board=cq.Compound.makeCompound(components)
# AABB culling excludes only components entirely inside the guaranteed empty
# core, below the four bosses (which start at Z14.8). Every other part is kept.
candidates=[]
for component in components:
    b=component.BoundingBox()
    inside=(b.xmin>-82.44 and b.xmax<82.44 and b.ymin>-47.95 and b.ymax<49.95
            and b.zmin>1.9 and b.zmax<14.79)
    if not inside:candidates.append(component)
print('Exact screen/case candidates',len(candidates),'of',len(components),flush=True)
check('installed_screen_vs_case',cq.Compound.makeCompound(candidates),body)
check('complete_touch_fpc_and_glass_vs_case',components[1337],body)
check('complete_lcd_fpc_and_metal_vs_case',components[1338],body)
# Independent ribbon-entry allowances cross the glass-seat edge all the way
# from the open front into the recess. The previous LCD roof blocked this path
# even though the installed vendor FPC posed no interference.
for name,x,width in [('touch',-64.,19.),('lcd',.5,29.)]:
    check(f'{name}_fpc_front_entry_open',box(width,1.6,10,x,-49.7,-.1),body)
check('speaker_vs_screen',pod,board)
check('pedestal_vs_screen',stand,board)
check('pedestal_vs_speaker',stand,pod)
for name,module,direction in [('speaker',pod,-1),('pedestal',stand,1)]:
    other=stand if name=='speaker' else pod
    for dz in [6,3,1,0]:
        moved=module.translate((0,-direction*8,dz))
        check(f'{name}_entry_normal_{dz}',moved,body)
        check(f'{name}_entry_normal_{dz}_vs_other_module',moved,other)
    for dy in [8,6,4,2,0]:
        moved=module.translate((0,-direction*dy,0))
        check(f'{name}_lower_{dy}',moved,body)
        check(f'{name}_lower_{dy}_vs_other_module',moved,other)
    # Gravity must push each joint into a positive stop, without a locking pin.
    ang=math.radians(20)
    gravity=(0,direction*.3*math.cos(ang),-direction*.3*math.sin(ang))
    v=module.translate(gravity).intersect(body).Volume()
    checks[f'{name}_gravity_seat_blocks_0p3mm']={'blocking_mm3':round(v,7),'pass':v>.01}
    print(f'{name}_gravity_seat_blocks_0p3mm',checks[f'{name}_gravity_seat_blocks_0p3mm'],flush=True)
    v=module.translate((0,0,1)).intersect(body).Volume()
    checks[f'{name}_wide_heads_prevent_normal_pullout']={'blocking_mm3':round(v,7),'pass':v>.01}
    print(f'{name}_wide_heads_prevent_normal_pullout',checks[f'{name}_wide_heads_prevent_normal_pullout'],flush=True)
    # Measure both directions using the real local joint, not just a far-away
    # pull-out obstruction. The previous check alone allowed visibly loose fits.
    row=20 if name=='speaker' else -28
    for x in SPEC['columns']:
        crop=box(24,40,13,x,row,14)
        local_case=body.intersect(crop);local_module=module.intersect(crop)
        def free_travel(sign):
            lo,hi=0.,1.
            for _ in range(12):
                mid=(lo+hi)/2
                v=local_module.translate((0,0,sign*mid)).intersect(local_case).Volume()
                if v>1e-6:hi=mid
                else:lo=mid
            return lo
        outward=free_travel(1);inward=free_travel(-1)
        checks[f'{name}_joint_{x}_axial_play']={
            'outward_mm':round(outward,4),'inward_mm':round(inward,4),
            'total_mm':round(outward+inward,4),'target_mm':SPEC['axial_play_target'],
            'intersection_threshold_mm3':1e-6,
            'pass':outward+inward<=.30}
        print('Axial play',name,x,checks[f'{name}_joint_{x}_axial_play'],flush=True)

for x in [-68,68]:
    airway=cq.Solid.makeCylinder(1.6,105,cq.Vector(x,-44.9,9.9))
    for name,shape in [('case',body),('pedestal',stand)]:
        # The case's own rear hole is already cut; test the whole acoustic ray.
        check(f'mic_{x}_clear_{name}',airway,shape)
for label,dims in [('min',(99,44,20.5)),('nominal',(99.5,44.5,20.8)),('max',(100,45,21.1))]:
    w,h,d=dims;speaker=box(w,h,d,0,14,47.0-d)
    check(f'speaker_envelope_{label}',speaker,pod)
rigid=pod.cut(read('speaker_clips'))
for dz in [-25,-10,0]:
    check(f'speaker_push_into_rigid_box_{dz}',box(100,45,21.1,0,14,25.9+dz),rigid)
for dy in [0,4,8]:
    route=wire_envelope(dy).translate((0,4,-.6))
    check(f'wire_{dy}_vs_case',route,body)
    check(f'wire_{dy}_vs_pod',route,pod.translate((0,dy,0)))
check('board_speaker_plug_allowance',board_plug_envelope(),body)
check('board_speaker_wire_channel',board_wire_envelope(),body)
check('board_speaker_wire_vs_electronics',board_wire_envelope(),board)
# A recessed path must leave a continuous outside skin, rather than an exposed slit.
for name,x,y,z in [('plug',*BOARD_PLUG_XY,21.05),('channel',-24.25,29.4675,21.0)]:
    probe=box(4,4,.9,x,y,z);missing=probe.cut(body).Volume()
    checks[f'{name}_recess_preserves_outer_skin']={'missing_mm3':round(missing,7),'pass':missing<.001}
# Preserve both the 1.5 mm inner land and the original continuous sidewall.
land_start=49.95-PLUG_WALL_LAND
wall_probe=box(12,50.8-land_start,2.5,BOARD_PLUG_XY[0],(50.8+land_start)/2,18.45)
missing=wall_probe.cut(body).Volume()
checks['plug_recess_sidewall_is_continuous']={'inner_land_mm':PLUG_WALL_LAND,
    'missing_mm3':round(missing,7),'pass':missing<.001}
check('TF_card_path',box(11.5,18,1.5,2.13,-51,8.85),body)
# A conservative ribbon-only probe through the requested top opening.
camera=box(18,15,.4,0,53.67,15.5)
check('top_camera_ribbon_exit',camera,body)
for name,shape in [('speaker',pod),('pedestal',stand)]:check(f'camera_exit_vs_{name}',camera,shape)
# The STEP's two glass outlines plus 0.1 mm overall manufacturing allowance.
lens=glass_envelope(.1)
for angle in [30,20,12,8,5,3,1,0]:
    check(f'max_lens_insertion_{angle}',lens.rotate((82.14,0,0),(82.14,1,0),-angle),body)
for dy in [-.1,.1]:check(f'glass_short_edge_allowance_{dy}',lens.translate((0,dy,0)),body)

# Same hook envelope fits either port orientation; no auxiliary fastener.
for y in SPEC['rows']:
    for x in SPEC['columns']:
        check(f'standard_tile_fits_at_{x}_{y}',tile(x,y),body)

notes={'revision':'current','screen_reference':reference_notes(),
       'screen_case_candidate_count':len(candidates),'total_screen_components':len(components),
       'candidate_culling':'Only AABBs wholly in guaranteed empty core X +/-82.44,Y[-47.95,49.95],Z(1.9,14.79) excluded.',
       'mechanical_only':'Gravity mount is a project mechanical interface, not an electrical standard.',
       'load':'Opposite slot orientations seat both loads under gravity; no auxiliary lock. Lift along the rear plane to remove.',
       'camera':'22 x 4 mm top-centre ribbon exit; no camera mount.',
       'printing':'Support disabled; geometry-audited continuous growth and short two-ended bridges.',
       'limitations':'Discrete positions, not continuous sweep, strength or fatigue simulation. No anti-lift retention is intended.',
       'physical_fit':'Maintainer physical prototype confirms glass fit. Open LCD FPC entry and other corrected features await another physical check.',
       'fpc_entry':'Independent front-to-recess ribbon allowance prisms check both entrances; installed vendor FPC clearance alone does not establish installability.',
       'hook_clearance':'Real local joints checked in both normal directions; target total free travel 0.25 mm.',
       'speaker_plug':'Board-side PH2.0 position from vendor model. Provisional 10 x 6.5 x 5.5 mm mating allowance; PH reference housing XY is 5.8 x 4.5 mm (JST ePH.pdf), not a measurement or identification of the user plug.'}
(OUT/'fit_validation.json').write_text(json.dumps({'checks':checks,'notes':notes,
    'model_source_sha256':model_sources(),'stl_sha256':stl_inputs(),
    'brep_sha256':hashes([OUT/f'{n}.brep' for n in ['shell','speaker','stand','speaker_clips']]),
    'vendor_sha256':source['sha256']},indent=2))
print('FIT_REPORT_SAVED',flush=True)
assert all(v['pass'] for v in checks.values()),[k for k,v in checks.items() if not v['pass']]
