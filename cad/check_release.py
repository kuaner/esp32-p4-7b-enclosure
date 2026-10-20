"""Validate distributed files and evidence using only the Python standard library."""
from pathlib import Path,PurePosixPath
import hashlib,json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/current'
V=OUT/'verification'
read=lambda name:json.loads((V/name).read_text())
manifest=read('release_sha256.json')
required={'README.md','LICENSE','AGENTS.md','CONTRIBUTING.md','THIRD_PARTY_NOTICES.md',
          'docs/DEVELOPMENT.md','.github/workflows/cad.yml','.github/workflows/release.yml',
          'output/current/README.md'}
required.update(str(p.relative_to(ROOT)) for p in (ROOT/'cad').iterdir()
                if p.suffix in ['.py','.json'] or p.name=='requirements.txt')
assert required<=manifest.keys(), 'Missing documentation or source in release manifest'
for name,digest in manifest.items():
    path=PurePosixPath(name)
    assert not path.is_absolute() and '..' not in path.parts, name
    assert not name.startswith('design/') and path.suffix not in ['.brep','.stp','.dwg','.pdf','.gcode'], name
    assert path.name!='.DS_Store', name
    actual=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    assert actual==digest, 'Release changed; regenerate checked package: '+name
parts=['01_DLC_shell','02_DLC_speaker','03_stand']
assert sorted(p.stem for p in (OUT/'STL').glob('*.stl'))==parts
for name in parts:
    for suffix,folder in [('stl','STL'),('step','STEP')]:
        assert f'output/current/{folder}/{name}.{suffix}' in manifest
build=read('print_validation.json');fit=read('fit_validation.json')
layer=read('support_free_geometry.json');sliced=read('slice_validation.json')
assert set(build['parts'])==set(parts) and all(
    p['valid_CAD'] and p['watertight'] and p['solids']==1 and abs(p['z_min'])<.001
    for p in build['parts'].values())
assert len(fit['checks'])==78 and all(p['pass'] for p in fit['checks'].values())
assert set(layer['parts'])==set(parts[1:]) and all(p['pass'] for p in layer['parts'].values())
assert set(sliced['parts'])==set(parts) and not sliced['support_enabled']
for name,p in sliced['parts'].items():
    assert p['pass'] and p['support_toolpath_seconds']==0 and not p['warning']
    assert p['input_sha256']==manifest[f'output/current/STL/{name}.stl']
for report in [build,fit,layer]:
    for field in ['model_source_sha256','stl_sha256']:
        assert report[field]
        for name,digest in report[field].items():assert manifest[name]==digest, name
expected=json.loads((ROOT/'cad/vendor_reference.json').read_text())
assert fit['vendor_sha256']==expected['sha256']
print(f'RELEASE_VERIFIED: {len(manifest)} files, 3 parts, 78 fit checks, 2 layer audits, 3 slices')
