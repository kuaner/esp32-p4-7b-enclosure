"""Compare rebuilt STL facets with the exact committed, sliced model inputs."""
from collections import Counter
from io import BytesIO
from pathlib import Path
import json
import subprocess

import numpy as np
from scipy.spatial import cKDTree
import trimesh

ROOT = Path(__file__).resolve().parents[1]
# Less than one micron; only accommodates platform floating-point output.
MAX_VERTEX_ERROR_MM = 0.00002


def oriented_faces(faces):
    """Ignore facet ordering and cyclic starts, but retain winding and multiplicity."""
    return Counter(min(tuple(f), tuple(np.roll(f, 1)), tuple(np.roll(f, 2)))
                   for f in faces)


def compare(reference, rebuilt):
    for mesh in (reference, rebuilt):
        assert mesh.is_watertight and mesh.is_winding_consistent
        assert len(mesh.split()) == 1
    assert len(reference.vertices) == len(rebuilt.vertices), 'Vertex count changed'
    assert len(reference.faces) == len(rebuilt.faces), 'Facet count changed'
    distances, mapping = cKDTree(reference.vertices).query(rebuilt.vertices)
    error = float(distances.max())
    assert error <= MAX_VERTEX_ERROR_MM, f'Vertex displacement: {error} mm'
    assert len(set(mapping)) == len(reference.vertices), 'Vertex correspondence is not bijective'
    assert oriented_faces(reference.faces) == oriented_faces(mapping[rebuilt.faces]), 'Facets or winding changed'
    return {'vertices': len(reference.vertices), 'facets': len(reference.faces),
            'max_vertex_error_mm': error}


if __name__ == '__main__':
    results = {}
    for name in ('shell', 'speaker', 'stand'):
        path = f'output/current/STL/{name}.stl'
        original = subprocess.run(['git', 'show', f'HEAD:{path}'], cwd=ROOT,
                                  check=True, capture_output=True).stdout
        reference = trimesh.load_mesh(BytesIO(original), file_type='stl')
        rebuilt = trimesh.load_mesh(ROOT / path)
        results[name] = compare(reference, rebuilt)
    print(json.dumps(results, indent=2))
