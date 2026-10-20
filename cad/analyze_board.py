"""Inspect the supplied manufacturer's STEP. All measurements are millimetres."""
from pathlib import Path
import json,hashlib,sys
import cadquery as cq
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_Label, TDF_LabelSequence
from OCP.TDataStd import TDataStd_Name

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'design' / 'reference'
OUT.mkdir(parents=True, exist_ok=True)
expected = json.loads((ROOT/'cad/vendor_reference.json').read_text())
src = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv)>1 else ROOT/expected['filename']
if not src.is_file():
    raise SystemExit('Manufacturer STEP missing. See docs/DEVELOPMENT.md: '+expected['filename'])
digest = hashlib.sha256(src.read_bytes()).hexdigest()
if digest != expected['sha256']:
    raise SystemExit('Unexpected manufacturer STEP hash. Component IDs require the documented reference.')
print('Loading', src.name, flush=True)
reader = STEPCAFControl_Reader()
reader.SetColorMode(False)
reader.SetNameMode(True)
reader.SetLayerMode(False)
reader.ReadFile(str(src))
print('STEP read; transferring', flush=True)
doc = TDocStd_Document(TCollection_ExtendedString('XCAF'))
reader.Transfer(doc)
print('Transferred; extracting parts', flush=True)
tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
labels = TDF_LabelSequence()
tool.GetFreeShapes(labels)

def name_of(label):
    attr = TDataStd_Name()
    return str(attr.Get().ToExtString()) if label.FindAttribute(TDataStd_Name.GetID_s(), attr) else ''

def walk(label, loc=cq.Location(), path=''):
    here = loc * cq.Location(tool.GetLocation_s(label))
    ref = TDF_Label()
    if tool.IsReference_s(label):
        tool.GetReferredShape_s(label, ref)
    else:
        ref = label
    name = name_of(ref) or name_of(label)
    path = path + '/' + name
    children = TDF_LabelSequence()
    tool.GetComponents_s(ref, children)
    if children.Length():
        for n in range(1, children.Length()+1):
            yield from walk(children.Value(n), here, path)
    else:
        yield cq.Shape.cast(tool.GetShape_s(ref)).moved(here), path

parts = []
for n in range(1, labels.Length()+1):
    parts.extend(walk(labels.Value(n)))
assert len(parts)==expected['components'], 'Unexpected component count'
rows = []
for i, (placed, name) in enumerate(parts):
    b = placed.BoundingBox()
    row = dict(id=i, name=name, bbox=[round(v, 5) for v in
        [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]],
        size=[round(b.xlen,5),round(b.ylen,5),round(b.zlen,5)],
        volume=round(placed.Volume(),5), color=None)
    rows.append(row)
    if max(b.xlen,b.ylen,b.zlen)>5:
        print(json.dumps(row), flush=True)
    # Compact individually named BREP components for later exact interference tests.
    placed.exportBrep(str(OUT / f'part_{i:04d}.brep'))
total = cq.Compound.makeCompound([p[0] for p in parts])
total.exportBrep(str(OUT / 'board_original.brep'))
(OUT / 'components.json').write_text(json.dumps(rows, indent=2))
(OUT / 'source.json').write_text(json.dumps({'filename':expected['filename'],
    'sha256':digest,'components':len(parts)},indent=2))
print('TOTAL', len(rows), total.BoundingBox().__dict__, flush=True)
