"""Layer footprint audit: self-support, new islands and two-ended short bridges.

This analyses geometry, independently of switching slicer supports off. It does
not simulate filament flow/cooling or prove physical print quality.
"""
from pathlib import Path
import json,math
import numpy as np
import trimesh
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from evidence import hashes,model_sources

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/current'
def audit(path,limit):
    m=trimesh.load_mesh(path)
    heights=np.arange(.10,m.bounds[1,2]-.0001,.2)
    sections=m.section_multiplane([0,0,0],[0,0,1],heights)
    previous=None;fail=[];bridges=[];islands=[];max_gap=0
    for h,section in zip(heights,sections):
        if section is None:continue
        current=unary_union(section.polygons_full).buffer(0)
        if previous is not None:
            polys=[current] if current.geom_type=='Polygon' else list(current.geoms)
            for p in polys:
                if p.area>.03 and p.intersection(previous.buffer(.25)).area<.001:
                    islands.append({'height':round(float(h),2),'area':round(p.area,4)})
            over=current.difference(previous.buffer(.28))
            pieces=[over] if over.geom_type=='Polygon' else list(getattr(over,'geoms',[]))
            for p in pieces:
                if p.area<.025:continue
                pts=[p.representative_point()]
                coords=list(p.exterior.coords)
                pts += [Point(v) for v in coords[::max(1,len(coords)//18)]]
                x0,y0,x1,y1=p.bounds
                if p.area>.15:
                    pts += [Point(x,y) for x in np.arange(x0+.2,x1,.5)
                            for y in np.arange(y0+.2,y1,.5) if p.contains(Point(x,y))]
                point=max(pts,key=lambda q:q.distance(previous))
                gap=point.distance(previous);max_gap=max(max_gap,gap)
                if gap<=.31:continue
                best=math.inf
                for angle in np.arange(0,180,10):
                    u=np.array([math.cos(math.radians(angle)),math.sin(math.radians(angle))])
                    pos=np.array([point.x,point.y]);line=LineString([pos-u*(limit+1),pos+u*(limit+1)])
                    # Endpoints may overlap the edge of a 0.4 mm extrusion.
                    hits=line.intersection(previous.buffer(.20))
                    hits=[hits] if hits.geom_type in ['LineString','Point'] else list(getattr(hits,'geoms',[]))
                    minus=[];plus=[]
                    for seg in hits:
                        cs=list(seg.coords)
                        ts=[float((np.array(v[:2])-pos)@u) for v in cs]
                        if not ts:continue
                        if max(ts)<0:minus.append(-max(ts))
                        elif min(ts)>0:plus.append(min(ts))
                    if minus and plus:
                        span=min(minus)+min(plus)
                        # The whole crossing must have material in this layer;
                        # do not mistake a cantilever around a hole for a bridge.
                        crossing=LineString([pos-u*min(minus),pos+u*min(plus)])
                        if crossing.difference(current.buffer(.04)).length<.12:best=min(best,span)
                item={'height':round(float(h),2),'gap_from_previous_mm':round(gap,3),
                      'point_xy':[round(point.x,3),round(point.y,3)],
                      'two_end_span_mm':round(best,3) if math.isfinite(best) else None,
                      'area_mm2':round(p.area,3)}
                if best<=limit+.15:bridges.append(item)
                else:fail.append(item)
        previous=current
    return {'file':path.name,'layer_height_mm':.2,'self_support_allowance_mm':.28,
            'layers_checked':len(heights),'bridge_limit_mm':limit,
            'maximum_gap_from_previous_mm':round(max_gap,3),
            'maximum_two_end_bridge_mm':max([v['two_end_span_mm'] for v in bridges],default=0),
            'bridge_regions':bridges,'unsupported_regions':fail,'new_islands':islands,
            'pass':not fail and not islands}

report={'revision':'current','parts':{},
        'method':'0.20 mm horizontal sections; previous-layer footprint; two-ended bridge tests with 0.20 mm bead overlap at anchors; separate from slicer support switch.',
        'limitation':'Geometric audit, not physical filament-flow or strength validation.'}
for name in ['02_DLC_speaker','03_stand']:
    print('Layer audit',name,flush=True)
    r=audit(OUT/'STL'/f'{name}.stl',4.5)
    report['parts'][name]=r
    print(name,'pass',r['pass'],'bridges',r['maximum_two_end_bridge_mm'],
          'unsupported',len(r['unsupported_regions']),'islands',len(r['new_islands']),flush=True)
report['model_source_sha256']=model_sources()
report['stl_sha256']=hashes([OUT/'STL'/f'{name}.stl' for name in report['parts']])
(OUT/'verification/support_free_geometry.json').write_text(json.dumps(report,indent=2))
assert all(r['pass'] for r in report['parts'].values())
