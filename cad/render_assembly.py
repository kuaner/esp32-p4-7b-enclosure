"""MakerWorld assembly sheets rendered from the current CAD solids.

The speaker is an explicitly labelled nominal-size envelope, not a detailed
manufacturer model. Screen rotation and module entry offsets follow the
existing assembly coordinates and discrete verification positions.
"""
from pathlib import Path
import math
import os

import cadquery as cq
from PIL import Image, ImageDraw, ImageFont

from fit_reference import component
from primitives import box
from render_cad import render

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/current'
DEST = OUT / 'previews'
read = lambda n: cq.Shape.importBrep(str(OUT / 'verification' / f'{n}.brep'))
body, pod, stand = (read(n) for n in ('shell', 'speaker', 'stand'))
GRAY = (.48, .54, .56)
DARK = (.26, .32, .35)
AMBER = (.90, .51, .17)
INK = '#203743'
MUTED = '#607681'
TEAL = '#147d8a'
ORANGE = '#d87a25'
PAGE = '#f6f8fa'
SCENE = '#edf2f7'
FONT = os.environ.get('CAD_CJK_FONT')
if not FONT:
    FONT = next((p for p in [
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simhei.ttf'
    ] if Path(p).is_file()), None)
if not FONT:
    raise SystemExit('Set CAD_CJK_FONT to a CJK .ttf or .ttc font.')
font = lambda n: ImageFont.truetype(FONT, n)
SIZE = (1000, 820)


def arrow(draw, start, end, color=ORANGE, width=8):
    a, b = tuple(start), tuple(end)
    draw.line([a, b], fill=color, width=width)
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    if length < 1:
        return
    ux, uy = dx / length, dy / length
    head = min(25, length * .4)
    draw.polygon([b, (b[0]-head*ux+head*.45*uy, b[1]-head*uy-head*.45*ux),
                  (b[0]-head*ux-head*.45*uy, b[1]-head*uy+head*.45*ux)], fill=color)


def motion_arrow(draw, start, end):
    # Enlarge the direction glyph for readability; the stated travel is 8 mm.
    dx, dy = end[0]-start[0], end[1]-start[1]
    length = math.hypot(dx, dy)
    mid = ((start[0]+end[0])/2, (start[1]+end[1])/2)
    unit = (dx/length, dy/length)
    arrow(draw, (mid[0]-48*unit[0], mid[1]-48*unit[1]),
          (mid[0]+48*unit[0], mid[1]+48*unit[1]))


def label(draw, text, xy, target=None, color=TEAL, size=29):
    f = font(size)
    bounds = draw.textbbox((0, 0), text, font=f)
    w, h = bounds[2] - bounds[0] + 32, 52
    x, y = xy
    if target is not None:
        anchor = (min(max(target[0], x+15), x+w-15), y+h/2)
        draw.line([anchor, target], fill=color, width=3)
        tx, ty = target
        draw.ellipse((tx-7, ty-7, tx+7, ty+7), fill=color)
    draw.rounded_rectangle((x, y, x+w, y+h), radius=12, fill='white', outline=color, width=2)
    draw.text((x+16, y+(h-(bounds[3]-bounds[1]))/2-bounds[1]), text, font=f, fill=color)


def scene(name, items, *, points=None, **kwargs):
    path = DEST / f'assembly_detail_{name}.png'
    projected = render(items, path, size=SIZE, projections=points, **kwargs)
    return Image.open(path).convert('RGB'), projected


def wrapped(draw, text, xy, width, size=32, fill=INK, spacing=16):
    f = font(size)
    y = xy[1]
    for paragraph in text.split('\n'):
        line = ''
        for c in paragraph:
            if line and draw.textlength(line+c, font=f) > width:
                draw.text((xy[0], y), line, font=f, fill=fill)
                y += size+spacing
                line = ''
            line += c
        if line:
            draw.text((xy[0], y), line, font=f, fill=fill)
            y += size+spacing
    return y


def sheet(name, number, title, subtitle, panels, note_title, note, footer):
    im = Image.new('RGB', (2200, 1720), PAGE)
    draw = ImageDraw.Draw(im)
    draw.rounded_rectangle((60, 48, 160, 132), radius=20, fill=TEAL)
    draw.text((80, 65), number, font=font(48), fill='white')
    draw.text((192, 55), title, font=font(63), fill=INK)
    draw.text((65, 157), subtitle, font=font(31), fill=MUTED)
    for i, (heading, picture, explanation) in enumerate(panels):
        x = 60 + i*1080
        draw.rounded_rectangle((x, 235, x+1040, 1380), radius=22, fill=SCENE,
                               outline='#d8e1e8', width=2)
        draw.text((x+28, 266), heading, font=font(37), fill=INK)
        im.paste(picture, (x+20, 340))
        wrapped(draw, explanation, (x+35, 1200), 970, size=32)
    draw.rounded_rectangle((60, 1440, 2140, 1640), radius=22, fill='#e7f0f2')
    draw.text((90, 1467), note_title, font=font(34), fill=TEAL)
    end = wrapped(draw, note, (90, 1524), 2010, size=31, fill=INK, spacing=12)
    assert end <= 1645, (name, end)
    draw.text((65, 1670), footer, font=font(23), fill=MUTED)
    path = DEST / f'assembly_{name}.png'
    im.save(path)
    print(path.name, flush=True)


print('Speaker and internal wiring', flush=True)
speaker = box(99.5, 44.5, 20.8, 0, 14, 26.2).translate((0, 0, -25))
pic, p = scene('speaker_insert', [(pod, GRAY), (speaker, AMBER, .72)],
    camera=(165, 130, -170), focus=(0, 14, 28), up=(0, 1, 0), scale=77,
    points={'from': (60, 14, 7), 'to': (60, 14, 40), 'grille': (0, 14, 51)})
d = ImageDraw.Draw(pic)
arrow(d, p['from'], p['to'])
label(d, '沿开口压入', (40, 55), color=ORANGE)
label(d, '振膜朝盒底格栅', (460, 710), p['grille'])
route = body.intersect(box(75, 48, 10, -24, 30, 15.5))
floor, other = [], []
for face in route.Faces():
    b = face.BoundingBox()
    is_floor = any(abs(b.zmin-z) < 1e-5 and abs(b.zmax-z) < 1e-5 for z in (20.9, 21.0))
    (floor if is_floor else other).append(face)
wire_pic, p = scene('wire_route', [(cq.Compound.makeCompound(other), GRAY),
                                 (cq.Compound.makeCompound(floor), AMBER)],
    camera=(-90, 95, -160), focus=(-24, 30, 20), up=(0, 1, 0), scale=39,
    points={'plug': (-48.5, 44.935, 20.9), 'out': (0, 14, 20.9)})
d = ImageDraw.Draw(wire_pic)
arrow(d, p['out'], p['plug'], color=TEAL, width=5)
label(d, '② 板端插头凹位', (575, 35), p['plug'])
label(d, '① 从居中孔穿入', (25, 700), p['out'])
sheet('speaker', '01', '先装喇叭，再接线理线',
      '接线与理线放在装屏前完成，喇叭盒最后再挂到主壳上。', [
          ('喇叭振膜朝格栅', pic, '支点托住喇叭框边，内部挡扣限位。\n如需防震，可在框边补薄双面胶。'),
          ('沿主壳内侧凹槽理线', wire_pic, '先让喇叭线从背面居中孔穿入壳内，\n接好板端插座，再将线理入凹位与线槽。')],
      '装屏前确认', '喇叭线留在槽内，避免被板卡压住；喇叭振膜不能贴胶或被支点顶住。',
      '实际 CAD 安装示意 · 左图橙色为喇叭尺寸占位；右图隐藏板卡，以橙色显示实际凹位与线槽。')


print('Screen insertion and four screws', flush=True)
axis = ((82.14, 0, 0), (82.14, 1, 0))
tilt = lambda s: s.rotate(*axis, -20)
screen = [(component(0), (.23, .39, .33)), (component(1338), (.66, .70, .72)),
          (component(1337), (.06, .08, .10)),
          (box(154.58, 86.42, .025, 1.79, 2.855, .005), (.075, .14, .19)),
          (cq.Compound.makeCompound([component(i) for i in range(1324, 1337)]), (.70, .72, .70))]
free = tilt(cq.Vertex.makeVertex(-76, 0, 0)).Center().toTuple()
screen_pic, p = scene('screen_insert', [(body, GRAY)]+[(tilt(s), c) for s, c in screen],
    camera=(210, 170, -280), focus=(0, 0, -12), up=(0, 1, 0), scale=100,
    points={'usb': (81.5, 17, 5), 'free': free, 'seat': (-76, 0, 0)})
d = ImageDraw.Draw(screen_pic)
arrow(d, p['free'], p['seat'])
label(d, '① 开关 / USB 侧先入', (35, 40), p['usb'])
label(d, '② 放下按键侧', (35, 720), color=ORANGE)
holes = {f'h{i}': (x, y, 22.2) for i, (x, y) in enumerate(
    [(-78, -43.5), (-78, 45.50005), (78.00009, -43.5), (78.00009, 45.50005)])}
screw_pic, p = scene('screen_screws', [(body, GRAY)], camera=(200, -120, 320),
    focus=(0, 0, 18), up=(0, 1, 0), scale=82, points=holes)
d = ImageDraw.Draw(screw_pic)
for x, y in p.values():
    d.ellipse((x-20, y-20, x+20, y+20), outline=ORANGE, width=6)
label(d, '4 × M2.5 × 8 mm 原螺丝', (280, 710), color=ORANGE)
sheet('screen', '02', '屏幕斜放入壳，再紧固',
      '保持已经打样确认的玻璃配合尺寸；图中放大展示安装动作。', [
          ('先入开关侧，再放下按键侧', screen_pic,
           '先斜放开关 / USB 端，再放下按键端。\n让触摸和 LCD 排线落入各自的开放缺口。'),
          ('从背面固定四个原孔位', screw_pic,
           '确认屏幕自然坐平后，再均匀紧固。\n使用原四颗螺丝，不需要预埋螺母。')],
      '先坐平，再拧螺丝', '屏幕若被排线或喇叭线顶起，先重新理线，不要用拧紧螺丝将它强行压平。',
      '实际 CAD 安装示意 · 屏幕尺寸已打样确认；最新排线开放入口仍待实物复测。')


print('Opposite gravity mounting directions', flush=True)
a = math.radians(20)
up = (0, math.cos(a), -math.sin(a))
hang_pic, p = scene('speaker_mount', [(body, GRAY), (pod.translate((0, 8, 6)), DARK, .73)],
    camera=(205, 115, 310), focus=(0, 10, 25), up=up, scale=85,
    points={'entry': (62.5, 28, 22), 'from': (82, 28, 29), 'to': (82, 20, 29)})
d = ImageDraw.Draw(hang_pic)
motion_arrow(d, p['from'], p['to'])
label(d, '对准宽口，先贴入', (30, 35), p['entry'])
label(d, '喇叭盒下滑 8 mm', (400, 715), color=ORANGE)
base_pic, p = scene('stand_mount', [(body.translate((0, 8, -6)), GRAY), (stand, DARK)],
    camera=(225, 125, 320), focus=(0, -5, 25), up=up, scale=100,
    points={'from': (93, -12, 22), 'to': (93, -20, 22), 'stand': (0, -74, 28)})
d = ImageDraw.Draw(base_pic)
motion_arrow(d, p['from'], p['to'])
label(d, '主机下放 8 mm', (25, 35), color=ORANGE)
label(d, '底座放稳不动', (385, 720), p['stand'])
sheet('mounts', '03', '挂接模块与拆卸方向',
      '上排挂喇叭，下排承托主机；两排挂槽的承重方向相反。', [
          ('上排：喇叭盒向下滑', hang_pic,
           '挂脚对准宽口，先贴入主壳。\n喇叭盒向下滑 8 mm，挂住后落座。'),
          ('下排：底座固定，主机向下放', base_pic,
           '底座放稳，对准下排挂点。\n主机沿背面下放 8 mm，落座后遮住挂槽。')],
      '拆卸与搬动', '反向抬起 8 mm 后再取下；搬动整机时同时托住底座。取下喇叭盒前先断开连接线。',
      '实际 CAD 安装示意 · 左图喇叭盒半透明以显示挂点；重力挂接，无独立防提脱锁扣。')
print('ASSEMBLY_SHEETS_READY', flush=True)
