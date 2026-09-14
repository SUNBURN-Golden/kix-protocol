"""Local acceptance-test CLI. Each invocation restarts the coordinator.

This stdin interface is trusted test administration, not a public API. Fixture
provider controls and performance completion deliberately require that context.
"""
import json
import sqlite3
import sys
from common import Rejected
from paid_integration import PaidCoordinator
from storage_receipt import StorageReceipt, StorageFault


def main():
    q = json.load(sys.stdin)
    # Acceptance runtime only. The newer task runtime lost committed state on
    # repeated child-process runs; do not silently continue money projections
    # under a configuration that has not passed this integration.
    if sys.version_info[:2] != (3, 12) or sqlite3.sqlite_version != "3.45.1":
        print(json.dumps({"ok": False, "error": "PAID_FIXTURE_REQUIRES_PYTHON_3_12_SQLITE_3_45_1",
                          "python": sys.version.split()[0], "sqlite": sqlite3.sqlite_version}))
        return 2
    c = None
    try:
        if q['action'] in ('recovery_inspect', 'recovery_apply'):
            from paid_recovery import Recovery
            recovery = Recovery(q['directory'])
            result = recovery.inspect() if q['action'] == 'recovery_inspect' else recovery.apply(q['params']['planId'])
            print(json.dumps({'ok': True, 'result': result}))
            return 0
        with StorageReceipt(q["directory"], q) as receipt:
            receipt.begin()
            c = PaidCoordinator(q["directory"], q["endpoint"])
            c.before_effect_submit = receipt.before_effect_submit
            a, p = q["action"], q.get("params", {})
            commands = {"prepare": c.prepare, "capture": c.capture, "sync_capture": c.sync_capture,
                        "record_submission": c.record_submission, "reconcile_chain": c.reconcile_chain,
                        "cancel": c.cancel, "fixture_complete_performance": c.release_after_fixture_performance,
                        "prepare_effect": c.prepare_effect, "send_effect": c.send_effect,
                        "sync_effect": c.sync_effect, "summary": c.summary}
            try:
                if a == "fixture_advance_provider":
                    result = c.provider.advance(**p)
                else:
                    if a not in commands:
                        raise Rejected("UNKNOWN_LOCAL_COMMAND")
                    result = commands[a](**p)
                response = {"ok": True, "result": result}
            except StorageFault:
                raise
            except (Rejected, ConnectionError) as error:
                response = {"ok": False, "error": str(error)}
            response["storageReceipt"] = receipt.finish(c)
            print(json.dumps(response))
            return 0 if response["ok"] else 2
    except StorageFault as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 2
    except (Rejected, ConnectionError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}))
        return 2
    finally:
        if c is not None:
            c.close()


if __name__ == "__main__":
    raise SystemExit(main())
