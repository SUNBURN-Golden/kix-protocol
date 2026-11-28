"""Read historical bootstrap-2 producer inputs for offline evidence checks."""

import gzip
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = 'sdk/conformance/fixtures/bootstrap-2-inputs.json.gz'


@lru_cache(maxsize=1)
def _snapshot(root):
    with gzip.open(root / SNAPSHOT, 'rt', encoding='utf-8') as archive:
        return json.load(archive)


def read_bootstrap_2_input(path, root=ROOT):
    """Read an archived input or a shared file still at its original path."""
    root = Path(root)
    archived = _snapshot(root).get(str(path))
    if archived is not None:
        return archived.encode('utf-8')
    return (root / path).read_bytes()
