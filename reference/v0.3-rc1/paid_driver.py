"""Local acceptance-test CLI. Each invocation restarts the coordinator.

This stdin interface is trusted test administration, not a public API. Fixture
provider controls and performance completion deliberately require that context.
"""
import json
import sys
from common import Rejected
from paid_integration import PaidCoordinator


def main():
    q = json.load(sys.stdin)
    c = PaidCoordinator(q["directory"], q["endpoint"])
    try:
        a, p = q["action"], q.get("params", {})
        commands = {"prepare": c.prepare, "capture": c.capture, "sync_capture": c.sync_capture,
                    "record_submission": c.record_submission, "reconcile_chain": c.reconcile_chain,
                    "cancel": c.cancel, "fixture_complete_performance": c.release_after_fixture_performance,
                    "prepare_effect": c.prepare_effect, "send_effect": c.send_effect,
                    "sync_effect": c.sync_effect, "summary": c.summary}
        if a == "fixture_advance_provider":
            result = c.provider.advance(**p)
        else:
            if a not in commands:
                raise Rejected("UNKNOWN_LOCAL_COMMAND")
            result = commands[a](**p)
        for db in (c.core.db, c.provider.db):
            if db.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                raise Rejected("LOCAL_DATABASE_INTEGRITY_FAILED")
        print(json.dumps({"ok": True, "result": result}))
    except (Rejected, ConnectionError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 2
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
