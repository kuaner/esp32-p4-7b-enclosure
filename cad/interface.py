"""Gravity hooks: one slot standard, installed in opposing orientations.

Engineering +Y is up. A hanging accessory slides down (direction=-1);
a fixed desktop base is the same interface turned over (direction=+1), so
the screen moves down onto it. There are no pins, latches or flexible detents.
"""
import cadquery as cq
from primitives import box,rr

SPEC=dict(tile_width=20.,tile_height=28.,plate_depth=4.4,column_pitch=125.,
          columns=[-62.5,62.5],rows=[20.,-28.],row_pitch=48.,travel=8.,
          orientations={'speaker':-1,'stand':1},entry=[10.,9.],neck=[4.8,16.7],
          stem=[4.2,8.],case_back_z=22.,case_inner_z=18.4,face_z=22.2,
          axial_play_target=.25,head_slope_depth=2.4,head_width=8.)

# The sloping shoulder meets the 4.8 mm slot edge before its narrow tip does.
# Dimension that contact, rather than treating the tip as a bearing surface.
HEAD_SLOPE=SPEC['head_slope_depth']/((SPEC['head_width']-SPEC['stem'][0])/2)
BEARING_Z=SPEC['case_inner_z']-(SPEC['axial_play_target']-(SPEC['face_z']-SPEC['case_back_z']))
HEAD_TOP_Z=BEARING_Z+HEAD_SLOPE*(SPEC['neck'][0]-SPEC['stem'][0])/2
HEAD_TIP_Z=HEAD_TOP_Z-SPEC['head_slope_depth']
SPEC.update(head_top_z=HEAD_TOP_Z,head_tip_z=HEAD_TIP_Z,
            effective_capture_depth=SPEC['face_z']-BEARING_Z,
            stem_depth=22.4-(HEAD_TOP_Z-.2))

def receiver(x,y,direction=-1):
    assert direction in [-1,1]
    entry=rr(10,9,.8,18.2,4.,x,y-direction*8)
    neck=box(4.8,16.7,4.,x,y-direction*4.15,18.2)
    return entry.fuse(neck)

def hanger(x=0,y=0):
    stem=box(4.2,8,SPEC['stem_depth'],x,y,HEAD_TOP_Z-.2)
    head=(cq.Workplane('XZ',origin=(x,y+4,0)).polyline([
        (-2.1,HEAD_TOP_Z),(2.1,HEAD_TOP_Z),(4,HEAD_TIP_Z),(-4,HEAD_TIP_Z)])
          .close().extrude(8).val())
    return stem.fuse(head)

def flat_adapter(x=0,y=0):
    return rr(20,28,3,22.2,4.4,x,y).fuse(hanger(x,y)).clean()

def receiver_coupon(direction=-1):
    return rr(24,36,3,18.4,3.6,y=-2*direction).cut(receiver(0,0,direction)).clean()
