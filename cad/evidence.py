"""Portable fingerprints shared by build, checks and packaging."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
MODEL_SOURCES = ('build_design.py', 'stand.py', 'interface.py', 'primitives.py',
                 'parameters.json')


def hashes(paths):
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


def model_sources():
    return hashes([ROOT / 'cad' / name for name in MODEL_SOURCES])


def stl_inputs():
    return hashes(list((ROOT / 'output/current/STL').glob('*.stl')))
