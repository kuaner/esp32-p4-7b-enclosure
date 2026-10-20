"""One-piece diamond upright, flat plinth and integral aperture covers."""
import math
import cadquery as cq
from primitives import box,rr
from interface import hanger

A=math.radians(20);C=math.cos(A);S=math.sin(A);GROUND=82*C
PARAMETERS=dict(foot_width=146.,foot_depth=104.,foot_thickness=4.5,
                lattice_width_top=136.,lattice_width_root=104.,
                lattice_depth=6.,lattice_holes=20,diamond_width=11.,diamond_height=15.,
                diamond_roof_angle_deg=round(math.degrees(math.atan(7.5/5.5)),3),
                stand_angle=20.,stand_hook_y=-28.,cover_max_width=18.,
                stand_style='one_piece_diamond_flat_base',assembly_pieces=1)

def to_print(shape):return shape.rotate((0,0,0),(1,0,0),110).translate((0,0,GROUND))
def to_engineering(shape):return shape.translate((0,0,-GROUND)).rotate((0,0,0),(1,0,0),-110)
def dh(y,z):return (S*y+C*z,C*y-S*z+GROUND)
def at_z(h,z):return z/C+(h-GROUND)*math.tan(A)
def xh_prism(points):
    return cq.Workplane('XZ',origin=(0,200,0)).polyline(points).close().extrude(400).val()
def profile_prism(points,width=400):
    return (cq.Workplane('YZ',origin=(-width/2,0,0)).polyline([(-d,h) for d,h in points])
            .close().extrude(width).val())
def xy_wire(points,h):
    return cq.Workplane('XY',origin=(0,0,h)).polyline([(x,-d) for x,d in points]).close().val()
def band_wire(half,outer,centre,h):
    return xy_wire([(-half,outer-3),(0,centre-3),(half,outer-3),
                    (half,outer+3),(0,centre+3),(-half,outer+3)],h)
def pad_wire(x,w,front,back,h):
    return xy_wire([(x-w/2,front),(x+w/2,front),(x+w/2,back),(x-w/2,back)],h)

def build_stand():
    foot=rr(146,104,14,0,4.5,y=-12)

    mid=at_z(37,30)+3;top=at_z(48.8,30)+3
    panel=cq.Solid.makeLoft([band_wire(52,34.9,11.5,3.5),
                            band_wire(68,mid,mid-.15,37),
                            band_wire(68,top,top-.15,48.8)],ruled=True)
    holes=[]
    for row,h in enumerate([13.5,26.,38.5]):
        centres=[-48,-32,-16,0,16,32,48] if row!=1 else [-40,-24,-8,8,24,40]
        for x in centres:
            holes.append(xh_prism([(x-5.5,h),(x,h-7.5),(x+5.5,h),(x,h+7.5)]))
    panel=panel.cut(cq.Compound.makeCompound(holes))

    # Integral cover rails reach the mating plane below the full T-slot.
    for sign in [-1,1]:
        pad=cq.Solid.makeLoft([
            pad_wire(sign*62.5,18,22,28,4),
            pad_wire(sign*62.5,18,at_z(30,22.2),at_z(30,36),30),
            pad_wire(sign*62.5,18,at_z(50.8,22.2),at_z(50.8,36),50.8)],ruled=True)
        panel=panel.fuse(pad)
    # Open chamfers around the microphone paths, rather than extra tunnels.
    # The boundary is <=65.42 at microphone Y=-44.9, outside its full 3.2 mm ray.
    right=(cq.Workplane('XY',origin=(0,0,-100)).polyline([
        (65,-150),(200,-150),(200,100),(71.5,100),
        (71.5,-36.2142857143),(65,-45.5)]).close().extrude(300).val())
    panel=panel.cut(to_print(right)).cut(to_print(right.mirror('YZ')))
    stand=to_engineering(foot.fuse(panel))
    features={}
    for x in [-62.5,62.5]:
        male=to_print(hanger(x,-28))
        d0,h0=dh(-32,22.4)
        lateral=xh_prism([(x-2.1,h0),(x+2.1,h0),(x+72.1,h0+100),(x-72.1,h0+100)])
        front=profile_prism([(d0,h0),(d0+100,h0),(d0+100,h0+100),(d0-70,h0+100)])
        male=male.intersect(lateral).intersect(front)
        stand=stand.fuse(to_engineering(male))
        features['hook_left' if x<0 else 'hook_right']=to_engineering(male)
    # The side chamfers keep the two microphone paths open.
    return stand.clean(),features
