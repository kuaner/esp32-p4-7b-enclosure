"""Conservative 3 mm wire-bundle envelope, for clearance views and checks.

This illustrative route does not prescribe the exact shape of a flexible lead.
The moving end follows the speaker box; the case feed-through stays fixed.
"""
import math
import cadquery as cq

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
