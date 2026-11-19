"""Record all changed paths and check source/document whitespace, excluding captures."""

import json
from pathlib import Path
import subprocess


evidence = Path(__file__).resolve().parent
paths = set(subprocess.check_output(['git', 'diff', '--name-only'], text=True).splitlines())
paths.update(subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'],
                                     text=True).splitlines())
paths.add(str(evidence.relative_to(Path.cwd()) / 'changed-paths.txt'))
(evidence / 'changed-paths.txt').write_text('\n'.join(sorted(paths)) + '\n')
captures = set()
for ledger in ('commands.json', 'transcripts.json'):
    for entry in json.loads((evidence / ledger).read_text()):
        captures.update(str(evidence.relative_to(Path.cwd()) / entry[key])
                        for key in ('stdout', 'stderr'))
for path in paths - captures:
    content = Path(path).read_text(encoding='utf-8')
    assert all(line == line.rstrip() for line in content.splitlines()), path
print(f'{len(paths)} changed paths recorded; source/document whitespace passed. '
      'Actual stdout/stderr captures retained verbatim, including prompt spaces.')
