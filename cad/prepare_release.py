"""Validate model evidence and write checksums; --manifest-only refreshes repository hashes."""
from pathlib import Path
import argparse,json,hashlib
from evidence import hashes,model_sources

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/current'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--manifest-only',action='store_true',help='Refresh repository file hashes and exit')
args=parser.parse_args()
read=lambda n:json.loads((OUT/'verification'/n).read_text())
pr=read('print_validation.json');fit=read('fit_validation.json')
layer=read('support_free_geometry.json');sliced=read('slice_validation.json')
assert pr['revision']==fit['notes']['revision']==layer['revision']==sliced['revision']=='current'
assert len(pr['parts'])==3 and all(v['valid_CAD'] and v['watertight'] and v['solids']==1 for v in pr['parts'].values())
assert len(fit['checks'])==92 and all(v['pass'] for v in fit['checks'].values())
assert len(layer['parts'])==2 and all(v['pass'] for v in layer['parts'].values())
assert len(sliced['parts'])==3 and all(v['pass'] for v in sliced['parts'].values())
for report in [pr,fit,layer]:
    assert report['model_source_sha256']==model_sources(), 'Geometry source changed; rebuild and recheck'
    for name,digest in report['stl_sha256'].items():
        assert hashes([ROOT/name])[name]==digest, 'Model changed; rerun checks: '+name
for name,digest in fit['brep_sha256'].items():
    # Local BREP is an optional intermediate, excluded from the public repository.
    # Clean CI checkouts use the committed exports, source fingerprints and reports.
    if (ROOT/name).exists():
        assert hashes([ROOT/name])[name]==digest, 'CAD changed; rerun fit checks: '+name
for name,r in sliced['parts'].items():
    assert hashlib.sha256((OUT/'STL'/f'{name}.stl').read_bytes()).hexdigest()==r['input_sha256']
files={}
def add(p,arc=None):
    assert p.is_file(),str(p)
    files[arc or str(p.relative_to(ROOT))]=p
for name in ['README.md','LICENSE','AGENTS.md','CONTRIBUTING.md','THIRD_PARTY_NOTICES.md',
             '.gitignore','.gitattributes','docs/DEVELOPMENT.md',
             '.github/workflows/cad.yml','.github/workflows/release.yml']:
    add(ROOT/name)
add(OUT/'README.md')
for folder,ext in [('STL','*.stl'),('STEP','*.step'),('verification','*.json')]:
    for p in sorted((OUT/folder).glob(ext)):
        if p.name!='release_sha256.json':add(p)
for name in ['overview','front','rear','exploded','stand','mounts','print_orientation','fit_details']:
    add(OUT/'previews'/f'{name}.png')
for pattern in ['*.py','*.json','requirements.txt']:
    for p in sorted((ROOT/'cad').glob(pattern)):add(p)
manifest={name:hashlib.sha256(p.read_bytes()).hexdigest() for name,p in files.items()}
if args.manifest_only:
    mp=OUT/'verification/release_sha256.json'
    mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
    print(json.dumps({'manifest_files':len(manifest),'archive_created':False}))
    raise SystemExit(0)
assets=[*sorted((OUT/'STL').glob('*.stl')),*sorted((OUT/'STEP').glob('*.step'))]
assert {p.name for p in assets}=={
    'shell.stl','speaker.stl','stand.stl','shell.step','speaker.step','stand.step',
    'assembly.step','expansion_adapter.step'}
(ROOT/'output/SHA256SUMS.txt').write_text(''.join(
    hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in assets))
print(json.dumps({'model_assets':len(assets),'archives':0,
                  'assembly_checks':len(fit['checks'])},ensure_ascii=False))
