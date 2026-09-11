"""Compare current result JSONs with one fresh verification run in the same environment."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
TARGETS=('acceptance_trace.json','verification.json')


def main():
    before={name:(ROOT/'results'/name).read_bytes() for name in TARGETS}
    subprocess.run([sys.executable,str(ROOT/'verify.py')],cwd=ROOT,check=True)
    checks={name:dict(byteIdentical=before[name]==(ROOT/'results'/name).read_bytes(),
        sha256=hashlib.sha256((ROOT/'results'/name).read_bytes()).hexdigest()) for name in TARGETS}
    report=dict(sameEnvironmentRequired=True,checks=checks,passed=all(x['byteIdentical'] for x in checks.values()))
    (ROOT/'results/reproducibility.json').write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.rglob('*'))
              if p.is_file() and '__pycache__' not in p.parts and p.name!='manifest.sha256.json' and p.suffix not in ('.db','.pyc')}
    (ROOT/'results/manifest.sha256.json').write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False)); return 0 if report['passed'] else 1


if __name__=='__main__': sys.exit(main())
