"""Run real Bambu CLI slices in the delivered orientation, with supports off.

The independent layer-footprint audit is check_printability.py. This script
checks actual toolpath generation and records settings/input hashes; it does
not assert that an automatic-support heuristic will never add optional support.
"""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/current'
APP=Path(os.environ.get('BAMBU_APP','/Applications/BambuStudio.app'))
EXE=APP/'Contents/MacOS/BambuStudio'
PROFILES=APP/'Contents/Resources/profiles/BBL'
MACHINE=PROFILES/'machine/Bambu Lab P1S 0.4 nozzle.json'
PROCESS={'type':'process','name':'ESP32 current 0.20 support-free audit',
    'inherits':'0.20mm Standard @BBL X1C','from':'user','instantiation':'true',
    'compatible_printers':['Bambu Lab P1S 0.4 nozzle'],
    'enable_support':'0','bridge_no_support':'1','layer_height':'0.2','wall_loops':'4',
    'sparse_infill_density':'15%','sparse_infill_pattern':'gyroid',
    'support_threshold_angle':'45','support_type':'normal(auto)',
    'brim_type':'no_brim','curr_bed_type':'Textured PEI Plate'}
def flatten_filament(name):
    p=PROFILES/'filament'/f'{name}.json'
    item=json.loads(p.read_text())
    parent=item.pop('inherits','')
    base=flatten_filament(parent) if parent else {}
    base.update(item)
    return base
filament=flatten_filament('Generic PETG')
filament.update(name='ESP32 current Generic PETG audit',**{'from':'user'})
report={'revision':'current','slicer':'Bambu Studio 02.08.02.61',
    'reference_printer':'Bambu Lab P1S 0.4 nozzle','filament':'Generic PETG',
    'layer_height_mm':.2,'support_enabled':False,'auto_orientation':False,
    'notes':['Reference profile is a verification setup, not a printer-specific G-code deliverable.',
             'Automatic supports can still be suggested for small bridges. Keep supports off.',
             'Geometry is checked separately; this slice is not a physical print test.'],
    'parts':{}}
with tempfile.TemporaryDirectory(prefix='esp32_current_slice_') as td:
    tmp=Path(td);settings=tmp/'process.json';settings.write_text(json.dumps(PROCESS))
    fila=tmp/'PETG.json';fila.write_text(json.dumps(filament))
    for stl in sorted((OUT/'STL').glob('*.stl')):
        print('Slice',stl.name,flush=True)
        dest=tmp/stl.stem
        args=[str(EXE),'--datadir',str(tmp/'userdata'),'--load-settings',f'{MACHINE};{settings}',
              '--load-filaments',str(fila),'--load-defaultfila','--load-filament-ids','1',
              '--arrange','1','--orient','0','--slice','0','--outputdir',str(dest),
              '--export-3mf','verification.3mf',str(stl)]
        p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        assert p.returncode==0,p.stdout[-3000:]
        result=json.loads((dest/'result.json').read_text());plate=result['sliced_plates'][0]
        gcode=(dest/'plate_1.gcode').read_text()
        assert '; enable_support = 0' in gcode and '; filament_type = PETG' in gcode
        times=plate['feature_type_times'];support=sum(v for k,v in times.items() if k.startswith('Support'))
        warning=plate.get('warning_message','')
        record={'input_sha256':hashlib.sha256(stl.read_bytes()).hexdigest(),
                'return_code':result['return_code'],'layers':gcode.count('; CHANGE_LAYER'),
                'support_toolpath_seconds':round(support,3),'warning':warning,
                'estimated_seconds':round(plate['total_predication']),
                'estimated_filament_g':round(sum(f['total_used_g'] for f in plate['filaments']),2),
                'bridge_toolpath_seconds':round(times.get('Bridge',0),1),
                'pass':result['return_code']==0 and support==0 and not warning}
        report['parts'][stl.stem]=record
        print(stl.stem,record,flush=True)
        assert record['pass'],record
(OUT/'verification/slice_validation.json').write_text(json.dumps(report,indent=2))
print('SLICE_VERIFIED',flush=True)
