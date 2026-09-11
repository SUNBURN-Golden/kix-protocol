"""Check packaged file hashes. Does not execute a chain or verify a ZK proof."""
from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'results/manifest.sha256.json').read_text())
bad=[]
for name,expected in manifest.items():
 p=(root/name).resolve()
 if not p.is_relative_to(root) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:bad.append(name)
print(json.dumps({'files':len(manifest),'hashesMatch':not bad,'mismatches':bad}))
sys.exit(1 if bad else 0)
