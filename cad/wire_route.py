"""Conservative 3 mm wire-bundle envelope, for clearance views and checks.

This illustrative route does not prescribe the exact shape of a flexible lead.
The moving end follows the speaker box; the case feed-through stays fixed.
"""
import math
import cadquery as cq
from primitives import rr,box

BOARD_PLUG_XY=(-48.5,44.935)
BOARD_WIRE_Z=19.2
CHANNEL_WIDTH=3.8
CHANNEL_TOP_Z=20.9
PLUG_WALL_LAND=1.5
PLUG_POCKET_HEIGHT=9.5
PLUG_ALLOWANCE=(10.,6.5,5.5)


def board_plug_recess(wall_y=49.95):
    # Leave a visible solid land; do not run the recess into the inner wall.
    centre_y=wall_y-PLUG_WALL_LAND-PLUG_POCKET_HEIGHT/2
    return rr(12,PLUG_POCKET_HEIGHT,2,18.3,2.7,BOARD_PLUG_XY[0],centre_y)


def board_wire_channel():
    a=BOARD_PLUG_XY;b=(0.,14.)
    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
    bar=box(length,CHANNEL_WIDTH,2.6,z=18.3).rotate(
        (0,0,0),(0,0,1),math.degrees(math.atan2(dy,dx))).translate(
        ((a[0]+b[0])/2,(a[1]+b[1])/2,0))
    for x,y in [a,b]:
        bar=bar.fuse(cq.Solid.makeCylinder(CHANNEL_WIDTH/2,2.6,cq.Vector(x,y,18.3)))
    return bar.clean()


def board_plug_envelope():
    # Provisional mating allowance, not a measured user part. PH reference body
    # is 5.8 x 4.5 mm in XY: https://www.jst-mfg.com/product/pdf/eng/ePH.pdf
    # Keep the broad X allowance; Y includes 1 mm each side of the reference body.
    w,h,d=PLUG_ALLOWANCE
    return rr(w,h,1,15.,d,*BOARD_PLUG_XY)


def board_wire_envelope(radius=1.5):
    points=[(*BOARD_PLUG_XY,BOARD_WIRE_Z),(0,14,BOARD_WIRE_Z),(0,14,23.0)]
    parts=[cq.Solid.makeSphere(radius,cq.Vector(*p),angleDegrees1=-90,angleDegrees2=90) for p in points]
    for a,b in zip(points,points[1:]):
        v=cq.Vector(*b)-cq.Vector(*a)
        parts.append(cq.Solid.makeCylinder(radius,v.Length,cq.Vector(*a),v.normalized()))
    return cq.Compound.makeCompound(parts)

def wire_envelope(dy=0.0,dz=0.0,radius=1.5):
    points=[(-51.8,10+dy,47.6+dz),(-51.8,10+dy,26.8+dz)]
    # 2 mm centreline bend inside the closed end pocket.
    for i in range(1,9):
        t=math.pi*i/16
        points.append((-49.8-2*math.cos(t),10+dy,26.8-2*math.sin(t)+dz))
    ux,uy=49.8,-dy
    length=math.hypot(ux,uy); ux/=length; uy/=length
    cx,cy=-2*ux,10-2*uy
    points.append((cx,cy,24.8+dz))
    # Turn down into the fixed feed-through; the 8 mm mounting movement is taken
    # up by the unrestrained wire in the air space behind the speaker.
    for i in range(1,9):
        t=math.pi*i/16
        points.append((cx+2*math.sin(t)*ux,cy+2*math.sin(t)*uy,22.8+2*math.cos(t)+dz))
    points.append((0,10,17.2))
    parts=[cq.Solid.makeSphere(radius,cq.Vector(*p),angleDegrees1=-90,angleDegrees2=90) for p in points]
    for a,b in zip(points,points[1:]):
        v=cq.Vector(*b)-cq.Vector(*a)
        parts.append(cq.Solid.makeCylinder(radius,v.Length,cq.Vector(*a),v.normalized()))
    return cq.Compound.makeCompound(parts)
