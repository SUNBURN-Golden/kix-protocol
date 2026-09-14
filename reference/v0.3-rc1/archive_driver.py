"""Trusted fixture administration: restore and reconcile; no money submission."""
import json
import sqlite3
import sys
from common import Rejected
from paid_archive import restore, reconcile


def main():
    q = json.load(sys.stdin)
    if sys.version_info[:2] != (3, 12) or sqlite3.sqlite_version != '3.45.1':
        print(json.dumps(dict(ok=False,error='PAID_FIXTURE_REQUIRES_PYTHON_3_12_SQLITE_3_45_1')))
        return 2
    try:
        if q['action'] == 'restore':
            result = restore(q['root'], q['stream'], q['target'], q.get('checkpoint'))
        elif q['action'] == 'reconcile':
            result = reconcile(q['target'], q['providerDatabase'])
        else:
            raise Rejected('UNKNOWN_ARCHIVE_COMMAND')
        print(json.dumps(dict(ok=True, result=result)))
        return 0
    except (Rejected, OSError, ValueError, KeyError, sqlite3.Error) as error:
        print(json.dumps(dict(ok=False,error=str(error))))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
