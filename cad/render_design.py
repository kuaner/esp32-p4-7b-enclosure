"""Review images rendered from the current, printable CAD solids."""
from pathlib import Path
import math,os
import cadquery as cq
from PIL import Image,ImageDraw,ImageFont
from render_cad import render
from primitives import box
from stand import to_print
from fit_reference import assembled_screen_component,component

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/current';DEST=OUT/'previews'
read=lambda n:cq.Shape.importBrep(str(OUT/'verification'/f'{n}.brep'))
body=read('01_DLC_shell');pod=read('02_DLC_speaker');stand=read('03_stand')
GRAY=(.48,.54,.56);DARK=(.26,.32,.35);BG='#f4f7f9';INK='#203743';MUTED='#607681'
FONT=os.environ.get('CAD_CJK_FONT')
if not FONT:
    candidates=['/System/Library/Fonts/STHeiti Medium.ttc',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                'C:/Windows/Fonts/msyh.ttc','C:/Windows/Fonts/simhei.ttf']
    FONT=next((p for p in candidates if Path(p).is_file()),None)
if not FONT:
    raise SystemExit('No CJK font found. Set CAD_CJK_FONT to a .ttf or .ttc path.')
font=lambda n:ImageFont.truetype(FONT,n)
a=math.radians(20);up=(0,math.cos(a),-math.sin(a))
glass=[(assembled_screen_component(1337),(.06,.08,.10)),
       (box(154.58,86.42,.025,1.79,2.855,.005),(.075,.14,.19))]
items=[(body,GRAY),(pod,DARK),(stand,DARK)]+glass
print('Assembly review',flush=True)
render(items,DEST/'front.png',camera=(-220,110,-320),up=up,size=(1600,1200))
render(items,DEST/'rear.png',camera=(230,135,300),up=up,size=(1600,1200))
render([(body,GRAY)]+glass+[(pod.translate((0,12,45)),DARK),
       (stand.translate((0,-18,60)),DARK)],DEST/'exploded.png',
       camera=(250,140,300),up=up,size=(1600,1200),scale=130)
sp=to_print(stand)
b=sp.BoundingBox();sp=sp.translate((0,-(b.ymin+b.ymax)/2,-b.zmin))
render([(sp,DARK)],DEST/'stand.png',camera=(155,185,125),up=(0,0,1),size=(1800,1200))

print('Mounting aperture concealment',flush=True)
crop=box(160,32,32,0,-32,8)
im=Image.new('RGB',(1800,1370),BG);d=ImageDraw.Draw(im)
d.text((45,25),'安装后，下排底座挂槽完整隐藏',font=font(44),fill=INK)
d.text((45,90),'遮孔面与底座是一体的；无需额外盖片、插销或紧固件。',font=font(28),fill=MUTED)
for i in range(2):
    its=[(body.intersect(crop),GRAY)]
    if i:its.append((stand.intersect(crop),DARK))
    path=DEST/f'mount_detail_{i}.png'
    render(its,path,camera=(0,-32,300),focus=(0,-32,24),up=(0,1,0),size=(1800,450),scale=23)
    im.paste(Image.open(path),(0,220+520*i))
    d.text((45,165+520*i),'装配前 · 主壳下排两个挂槽' if i==0 else '装配后 · 上端贴合面遮住整条挂槽',font=font(30),fill=INK)
d.text((45,1285),'几何检查包含挂槽轮廓外扩 1 mm 的遮挡范围；麦克风声路从两侧让开。',font=font(27),fill=MUTED)
im.save(DEST/'mounts.png')

print('Print orientations',flush=True)
im=Image.new('RGB',(2100,1070),BG);d=ImageDraw.Draw(im)
d.text((45,24),'当前设计 · 三个一体件 · 保持方向，关闭支撑',font=font(43),fill=INK)
shapes=[body.rotate((0,0,0),(1,0,0),180).translate((0,0,22)),
        pod.rotate((0,0,0),(1,0,0),180).translate((0,0,52)),sp]
for i,shape in enumerate(shapes):
    b=shape.BoundingBox();shape=shape.translate((0,-(b.ymin+b.ymax)/2,-b.zmin))
    plate=box(b.xlen+10,b.ylen+10,1,z=-1)
    path=DEST/f'print_{i}.png'
    render([(shape,DARK),(plate,(.78,.82,.85))],path,camera=(180,-150,170),up=(0,0,1),size=(700,700))
    im.paste(Image.open(path),(700*i,180))
    d.text((700*i+25,130),['主壳：背面贴床','喇叭盒：网孔底贴床','底座：平整底盘贴床'][i],font=font(28),fill=INK)
d.text((45,940),'菱形立架与底盘连成一个实体，不拆件；侧面接口与相机开口仍包含桥接。',font=font(28),fill=INK)
d.text((45,995),'依据实物反馈修正；已做 CAD 与参考切片检查，修正后的配合仍待实物复测。',font=font(27),fill=MUTED)
im.save(DEST/'print_orientation.png')

im=Image.new('RGB',(2000,1500),BG);d=ImageDraw.Draw(im)
d.text((45,24),'当前设计 · 一体菱形立架 + 平整底盘',font=font(45),fill=INK)
d.text((45,93),'免支撑 / 不拆底座 / 挂槽完整隐藏 / 无独立锁扣',font=font(29),fill=MUTED)
for i,(name,label) in enumerate([('stand.png','底座 · 菱形镂空，平整圆角底盘'),
                               ('rear.png','整机背面 · 底座安装孔已遮住'),
                               ('front.png','整机正面 · 底盘平整'),
                               ('mounts.png','下排挂槽 · 装配前后遮挡关系')]):
    x=25+i%2*1000;y=155+i//2*615
    pic=Image.open(DEST/name).convert('RGB');pic.thumbnail((950,510))
    im.paste(pic,(x+(950-pic.width)//2,y+(510-pic.height)//2))
    d.text((x+18,y+527),label,font=font(27),fill=INK)
d.text((45,1440),'实际 CAD 渲染；依据实物反馈修正，当前配合待复测。',font=font(27),fill=MUTED)
im.save(DEST/'overview.png')

print('Prototype corrections: actual sections and internal routing',flush=True)
detail_specs=[]
screen_crop=box(1.2,12,8,50,-49,-.5)
detail_specs.append(('edge',[(body.intersect(screen_crop),GRAY),
    (component(1337).intersect(screen_crop),(.10,.17,.19)),
    (component(1338).intersect(screen_crop),(.68,.72,.73))],
    dict(camera=(-150,-65,7),focus=(50,-49,2.5),up=(0,0,1),scale=6)))
fpc_crop=box(115,14,12.5,-26,-47.5,0)
touch_loop=component(1337).intersect(box(23,3.7,11,-64,-50.95,.251))
lcd_loop=component(1338).intersect(box(31,3.4,8,.5,-48.5,2.2))
detail_specs.append(('fpc',[(body.intersect(fpc_crop),GRAY),
    (touch_loop,(.86,.48,.15)),(lcd_loop,(.86,.48,.15))],
    dict(camera=(-115,35,-90),focus=(-26,-47,4),up=(0,0,1),scale=36)))
joint_crop=box(16,1.5,14,-62.5,20,14)
detail_specs.append(('hook',[(body.intersect(joint_crop),GRAY),
    (pod.intersect(joint_crop),(.83,.46,.15))],
    dict(camera=(-62.5,-150,20),focus=(-62.5,20,20),up=(0,0,1),scale=8)))
route_crop=box(75,48,10,-24,30,15.5)
route_detail=body.intersect(route_crop)
floor_faces=[];other_faces=[]
for face in route_detail.Faces():
    b=face.BoundingBox()
    is_floor=any(abs(b.zmin-z)<1e-5 and abs(b.zmax-z)<1e-5 for z in [20.9,21.0])
    (floor_faces if is_floor else other_faces).append(face)
detail_specs.append(('route',[(cq.Compound.makeCompound(other_faces),GRAY),
    (cq.Compound.makeCompound(floor_faces),(.86,.48,.15))],
    dict(camera=(-90,95,-160),focus=(-24,30,20),up=(0,1,0),scale=35)))
im=Image.new('RGB',(2000,1520),BG);d=ImageDraw.Draw(im)
d.text((45,24),'实物反馈修正 · 实际 CAD 剖面与内侧结构',font=font(42),fill=INK)
labels=[('屏幕短边 · 前后两级玻璃轮廓','玻璃前沿 99.17 mm，后部 98.77 mm；长边保持原尺寸。'),
        ('局部排线避让 · 保留完整原厂 FPC','触摸排线根部开台阶缺口；LCD 排线设局部斜顶凹位。'),
        ('挂钩夹持 · 名义总余量 0.25 mm','橙色为真实喇叭挂钩剖面；底座同步采用较短夹持段。'),
        ('喇叭插头凹位 + 内侧走线槽','橙色为真实凹位和槽底；12×12 mm 凹位接 3.8 mm 槽。')]
for i,(name,its,kwargs) in enumerate(detail_specs):
    path=DEST/f'detail_{name}.png'
    render(its,path,size=(940,500),**kwargs)
    x=25+i%2*1000;y=115+i//2*650
    im.paste(Image.open(path),(x,y))
    d.text((x+18,y+515),labels[i][0],font=font(29),fill=INK)
    d.text((x+18,y+566),labels[i][1],font=font(23),fill=MUTED)
d.text((45,1455),'已完成几何与参考切片检查；插头配合和修正后的松紧仍需实物复测。',font=font(27),fill=MUTED)
im.save(DEST/'fit_details.png')
print('REVIEW_IMAGES_READY',flush=True)
