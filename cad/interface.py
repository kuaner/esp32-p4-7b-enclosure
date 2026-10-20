"""DLC gravity hooks: one slot standard, installed in opposing orientations.

Engineering +Y is up. A hanging accessory slides down (direction=-1);
a fixed desktop base is the same interface turned over (direction=+1), so
the screen moves down onto it. There are no pins, latches or flexible detents.
"""
import cadquery as cq
from primitives import box,rr

SPEC=dict(tile_width=20.,tile_height=28.,plate_depth=4.4,column_pitch=125.,
          columns=[-62.5,62.5],rows=[20.,-28.],row_pitch=48.,travel=8.,
          orientations={'speaker':-1,'stand':1},entry=[10.,9.],neck=[4.8,16.7],
          stem=[4.2,8.],case_back_z=22.,face_z=22.2)

def receiver(x,y,direction=-1):
    assert direction in [-1,1]
    entry=rr(10,9,.8,18.2,4.,x,y-direction*8)
    neck=box(4.8,16.7,4.,x,y-direction*4.15,18.2)
    return entry.fuse(neck)

def hanger(x=0,y=0):
    stem=box(4.2,8,4.5,x,y,17.9)
    head=(cq.Workplane('XZ',origin=(x,y+4,0)).polyline([
        (-2.1,18.1),(2.1,18.1),(4,15.7),(-4,15.7)])
          .close().extrude(8).val())
    return stem.fuse(head)

def flat_adapter(x=0,y=0):
    return rr(20,28,3,22.2,4.4,x,y).fuse(hanger(x,y)).clean()

def receiver_coupon(direction=-1):
    return rr(24,36,3,18.4,3.6,y=-2*direction).cut(receiver(0,0,direction)).clean()
