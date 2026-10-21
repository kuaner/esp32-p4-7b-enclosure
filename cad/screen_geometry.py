"""STEP glass profiles and local FPC clearances, in assembly coordinates."""
import cadquery as cq
from primitives import box

# Front lip and rear glass are different outlines in the manufacturer's solid.
GLASS_FRONT=(164.28,99.17,.25)
GLASS_REAR=(163.88,98.77,1.65)
SCREEN=dict(width=171.,height=105.17,pocket_width=165.08,pocket_height=99.17,
            pocket_y=.5,enclosure_y=.5,glass_clearance_y_each=.2,
            glass_front_outline=list(GLASS_FRONT),glass_rear_outline=list(GLASS_REAR),
            front_mouth_height=99.77,front_lip_pocket_height=99.57,
            screen_reference_basis='STEP glass profiles; local FPC loops retained')


def glass_envelope(tolerance=.1):
    return box(GLASS_FRONT[0]+tolerance,GLASS_FRONT[1]+tolerance,.25,y=.5).fuse(
        box(GLASS_REAR[0]+tolerance,GLASS_REAR[1]+tolerance,1.65,y=.5,z=.25))


def flex_reliefs():
    # Both FPCs must enter from the open screen face. A roof can clear the
    # installed vendor pose yet trap the real ribbon during screen insertion.
    # Extend beyond the glass seat edge so no front lip remains across either entry.
    profiles={
        'touch_fpc':(-74.5,21.,[(-46.9,-.01),(-50.7,-.01),
                               (-50.7,10.8),(-46.9,10.8)]),
        'lcd_fpc':(-14.8,30.6,[(-46.8,-.01),(-50.7,-.01),
                               (-50.7,10.1),(-46.8,10.1)])}
    return {name:(cq.Workplane('YZ',origin=(x,0,0)).polyline(points).close()
                  .extrude(width).val()) for name,(x,width,points) in profiles.items()}
