"""Current design: one-piece diamond stand, flat plinth and concealed receivers.

Engineering frame is unchanged. Desktop parts are designed in actual printing
coordinates for continuous layerwise growth without disposable supports.
"""
from pathlib import Path
import json,math
import cadquery as cq
import trimesh
from primitives import box,rr
from interface import SPEC,receiver,hanger,flat_adapter
from stand import build_stand,to_print,PARAMETERS as STAND_PARAMETERS
from evidence import model_sources,stl_inputs
from screen_geometry import SCREEN,flex_reliefs
from wire_route import (board_plug_recess,board_wire_channel,BOARD_PLUG_XY,CHANNEL_WIDTH,
                        PLUG_WALL_LAND,PLUG_POCKET_HEIGHT,PLUG_ALLOWANCE)

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/current'
for name in ['STL','STEP','previews','verification']:
    (OUT/name).mkdir(parents=True,exist_ok=True)
P=json.loads((ROOT/'cad/parameters.json').read_text())
P.update(revision='current',speaker_front_z=47.0,pod_front_width=145.,pod_rear_width=116.,
         pod_inner=[101.,46.,27.5],pod_radius=6.0,maximum_module_short_bridge=4.5)
P.update(STAND_PARAMETERS)
P.update(SCREEN)
P.update(flex_relief='Both touch and LCD FPC notches open through the screen face; complete FPC geometry retained',
         speaker_plug_pocket=[12,PLUG_POCKET_HEIGHT,2.6],speaker_plug_xy=list(BOARD_PLUG_XY),
         speaker_plug_pocket_limit_y=49.95-PLUG_WALL_LAND,
         speaker_plug_wall_land=PLUG_WALL_LAND,speaker_plug_allowance=list(PLUG_ALLOWANCE),
         speaker_wire_channel_width=CHANNEL_WIDTH,speaker_wire_channel_depth=2.5,
         physical_status='Glass fit confirmed by physical prototype; open LCD FPC entry awaits recheck')
P['interface']=SPEC.copy()
P['stand_hook_y']=-28.0
P['stand_hook_head_width']=8.0
P['speaker_hook_head_width']=8.0


print('Screen shell: downward hanging speaker, reversed gravity-seated base',flush=True)
body=rr(P['width'],P['height'],5,0,22,y=.5)
body=body.cut(box(165.08,P['pocket_height'],2.9,y=.5,z=-1)).cut(
    box(P['core_width'],P['core_height'],16.5,y=P['core_y'],z=1.9))
lead=(cq.Workplane('XY',origin=(0,.5,-.01)).rect(166.28,P['front_mouth_height'])
      .workplane(offset=.31).rect(165.68,P['front_lip_pocket_height'])
      .workplane(offset=.30).rect(165.08,P['pocket_height']).loft(ruled=True).val())
body=body.cut(lead)
for relief in flex_reliefs().values():body=body.cut(relief)
for x,y in [(-78,-43.5),(-78,45.50005),(78.00009,-43.5),(78.00009,45.50005)]:
    body=body.fuse(cq.Solid.makeCylinder(4,3.7,cq.Vector(x,y,14.8)))
    body=body.cut(cq.Solid.makeCylinder(1.4,8,cq.Vector(x,y,14.7)))
    body=body.cut(cq.Solid.makeCylinder(2.6,2.2,cq.Vector(x,y,20)))
for x,y,z,w,h in [(84,-33.915,9.97,12.4,6.4),(84,-18.65005,9.97,12.4,6.4),
                  (84,.1,10.8,16.8,10.6),(84,34.4178,9.45,14.2,7.4),(-84,33.80051,10.45,17.2,7.4)]:
    opening=(cq.Workplane('YZ',origin=(x-6,y,z)).sketch().rect(w,h).vertices()
             .fillet(1).finalize().extrude(12).val());body=body.cut(opening)
for x,y,z,w,h,r in [(2.13,-44,10.1,19,6.2,.8),(0,60,14.3,22,4,.8)]:
    opening=(cq.Workplane('XZ',origin=(x,y,z)).sketch().rect(w,h).vertices().fillet(r)
             .finalize().extrude(14 if x else 20).val());body=body.cut(opening)
for x in [-68,68]:body=body.cut(cq.Solid.makeCylinder(1.6,4.3,cq.Vector(x,-44.9,17.9)))
for x in range(-32,33,8):
    for y in [-32,-40]:body=body.cut(rr(4.5,2,.9,18.2,4,x,y))
body=body.cut(rr(10,7,1.3,18.2,4,0,14))
body=body.cut(board_plug_recess(P['core_y']+P['core_height']/2)).cut(board_wire_channel())
for y,direction in [(20,-1),(-28,1)]:
    for x in SPEC['columns']:body=body.cut(receiver(x,y,direction))
body=body.clean()

print('Speaker: continuously growing shoulders, no overhanging ears',flush=True)
def wire_at(w,h,r,z):
    face=min(rr(w,h,r,z,.01,y=14).Faces(),key=lambda f:f.Center().z)
    return face.outerWire()
pod=cq.Solid.makeLoft([wire_at(116,54,6,52),wire_at(145,54,6,22.2)],ruled=True)
pod=pod.cut(rr(101,46,1,22.1,27.5,y=14))
pod=pod.cut(box(5.5,9,27.6,x=-50.75,y=14,z=22.1))
for i in range(-8,9):
    x=i*5.5;u=max(0,abs(x)-38);half=10+math.sqrt(max(0,100-u*u))
    pod=pod.cut(rr(2,2*half-4,.95,49.4,2.9,x,14))
for x in [-45.6,45.6]:
    for y in [-4.1,32.1]:pod=pod.fuse(cq.Solid.makeCylinder(3,5.0,cq.Vector(x,y,47.0)))
clips=[]
for sign in [1,-1]:
    relief=box(12,5,21.8,y=38,z=22.2)
    beam=box(10,1.2,18.2,y=37.6,z=26)
    # Grows inward along a 51-degree ramp in the supplied printing direction.
    tooth=(cq.Workplane('YZ',origin=(-5,0,0)).polyline([
        (37,26.4),(35.7,24.8),(35.7,24.5),(37,24.5)]).close().extrude(10).val())
    clip=beam.fuse(tooth)
    if sign<0:relief=relief.mirror('XZ',(0,14,0));clip=clip.mirror('XZ',(0,14,0))
    pod=pod.cut(relief).fuse(clip);clips.append(clip)
for x in SPEC['columns']:
    pod=pod.fuse(hanger(x,20))
pod=pod.clean()

print('Stand: one-piece diamond upright, flat plinth and covered mounting slots',flush=True)
stand,features=build_stand()
for name,shape in features.items():shape.exportBrep(str(OUT/'verification'/f'feature_stand_{name}.brep'))

parts={'shell':body,'speaker':pod,'stand':stand}
report={'revision':'current','parameters':P,'parts':{},
        'quantity':{'shell':1,'speaker':1,'stand':1},
        'notes':['No locking keys, pin holes, access windows or separate lids.',
                 'Speaker slides down. Screen moves down onto the reversed base slots.',
                 'Three printed pieces; stand and flat plinth form one solid.',
                 'Complete lower mounting apertures are covered by integral pads.',
                 'Physical prototype confirms glass fit; the open LCD FPC entry and other corrected features require a physical recheck.']}
for name,shape in parts.items():
    print('Export',name,flush=True)
    assert shape.isValid() and len(shape.Solids())==1,(name,len(shape.Solids()))
    shape.exportBrep(str(OUT/'verification'/f'{name}.brep'))
    cq.exporters.export(shape,str(OUT/'STEP'/f'{name}.step'))
    if name in ['shell','speaker']:
        printable=shape.rotate((0,0,0),(1,0,0),180).translate((0,0,22 if name=='shell' else 52))
    else:printable=to_print(shape)
    b=printable.BoundingBox();printable=printable.translate((0,-(b.ymin+b.ymax)/2,-b.zmin))
    path=OUT/'STL'/f'{name}.stl'
    cq.exporters.export(printable,str(path),tolerance=.035,angularTolerance=.10)
    mesh=trimesh.load_mesh(path)
    assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1,name
    report['parts'][name]={'valid_CAD':True,'watertight':True,'solids':1,
        'bbox_mm':[round(float(v),3) for v in mesh.extents],
        'volume_cm3':round(shape.Volume()/1000,3),'z_min':round(float(mesh.bounds[0,2]),6)}
    print(report['parts'][name],flush=True)
cq.Compound.makeCompound(clips).exportBrep(str(OUT/'verification/speaker_clips.brep'))
assembly=cq.Assembly(name='ESP32_P4_enclosure')
for name,col in [('shell',(.48,.54,.56)),('speaker',(.26,.32,.35)),('stand',(.26,.32,.35))]:
    assembly.add(parts[name],name=name,color=cq.Color(*col))
assembly.export(str(OUT/'STEP/assembly.step'))
# Standard flat-print test adapter; follows the speaker printing direction.
adapter=flat_adapter()
adapter.exportBrep(str(OUT/'verification/adapter_tile.brep'))
cq.exporters.export(adapter,str(OUT/'STEP/expansion_adapter.step'))
(ROOT/'cad/parameters.json').write_text(json.dumps(P,indent=2))
report.update(model_source_sha256=model_sources(),stl_sha256=stl_inputs())
(OUT/'verification/print_validation.json').write_text(json.dumps(report,indent=2))
print('CURRENT_DESIGN_BUILT',flush=True)
