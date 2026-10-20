"""Shared millimetre CAD primitives."""
import cadquery as cq

def box(w,h,d,x=0,y=0,z=0):
    return cq.Solid.makeBox(w,h,d,cq.Vector(x-w/2,y-h/2,z))

def rr(w,h,r,z,d,x=0,y=0):
    return (cq.Workplane('XY').sketch().rect(w,h).vertices().fillet(r)
            .finalize().extrude(d).translate((x,y,z)).val())
