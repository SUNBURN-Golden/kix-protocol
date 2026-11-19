"""Compare complete service envelopes, allowing guided opening-entry prompts."""

import json
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parent


def replies(text):
    result = []
    for line in text.splitlines():
        start = line.find('{"')
        if start >= 0:
            value = json.loads(line[start:])
            if 'provenance' in value:
                result.append(value)
    return result


for name, expected_exit in (('journey', 0), ('boundaries', 1)):
    outputs = [(EVIDENCE / f'{mode}-{name}.stdout').read_text()
               for mode in ('subprocess', 'in-process', 'guided')]
    assert outputs[0] == outputs[1], name
    envelopes = [replies(text) for text in outputs]
    assert envelopes[0] == envelopes[1] == envelopes[2], name
    assert envelopes[0][0]['operation'] == 'initialize', name
    assert envelopes[0][-1]['operation'] == 'view', name
    if name == 'boundaries':
        assert [row['error']['code'] for row in envelopes[0] if 'error' in row] == [
            'POOL_FORBIDDEN_FOR_TOKEN_SPEND'] * 3 + ['POOL_EXHAUSTED_PAUSED']
    for mode in ('subprocess', 'in-process', 'guided'):
        assert not (EVIDENCE / f'{mode}-{name}.stderr').read_bytes()
        assert int((EVIDENCE / f'{mode}-{name}.exit').read_text()) == expected_exit
    print(f'{name}: {len(envelopes[0])} complete envelopes MATCH across three modes; '
          f'fixture/live stdout byte-identical; stderr empty; expected exit {expected_exit}')
