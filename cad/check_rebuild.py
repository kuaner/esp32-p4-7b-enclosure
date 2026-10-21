"""Compare rebuilt CAD solids against the committed models with slice evidence.

Open CASCADE triangulation can differ by platform. Compare the actual solids,
then publish the exact committed STL bytes rather than un-sliced new meshes.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import subprocess

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
MAX_BOUND_ERROR_MM = 0.000001
MAX_VOLUME_ERROR_MM3 = 0.0001


def compare(reference, rebuilt):
    for shape in (reference, rebuilt):
        assert shape.isValid() and shape.Solids(), 'Invalid CAD'
    assert len(reference.Solids()) == len(rebuilt.Solids()), 'Solid count changed'
    a, b = reference.BoundingBox(), rebuilt.BoundingBox()
    bound_error = max(abs(getattr(a, field) - getattr(b, field))
                      for field in ('xmin', 'xmax', 'ymin', 'ymax', 'zmin', 'zmax'))
    assert bound_error <= MAX_BOUND_ERROR_MM, f'Bounds changed: {bound_error} mm'
    volume_error = abs(reference.Volume() - rebuilt.Volume())
    assert volume_error <= MAX_VOLUME_ERROR_MM3, f'Volume changed: {volume_error} mm3'
    missing = reference.cut(rebuilt)
    added = rebuilt.cut(reference)
    assert missing.isValid() and added.isValid(), 'Solid difference failed'
    missing_volume, added_volume = missing.Volume(), added.Volume()
    assert missing_volume <= MAX_VOLUME_ERROR_MM3, f'Missing material: {missing_volume} mm3'
    assert added_volume <= MAX_VOLUME_ERROR_MM3, f'Added material: {added_volume} mm3'
    return {'solids': len(reference.Solids()), 'max_bound_error_mm': bound_error,
            'volume_error_mm3': volume_error,
            'missing_mm3': missing_volume, 'added_mm3': added_volume}


if __name__ == '__main__':
    results = {}
    with TemporaryDirectory(prefix='cad-rebuild-') as tmp:
        for name in ('shell', 'speaker', 'stand', 'assembly', 'expansion_adapter'):
            path = f'output/current/STEP/{name}.step'
            original = subprocess.run(['git', 'show', f'HEAD:{path}'], cwd=ROOT,
                                      check=True, capture_output=True).stdout
            reference_path = Path(tmp) / f'{name}.step'
            reference_path.write_bytes(original)
            reference = cq.importers.importStep(str(reference_path)).val()
            rebuilt = cq.importers.importStep(str(ROOT / path)).val()
            results[name] = compare(reference, rebuilt)
    print(json.dumps(results, indent=2))
