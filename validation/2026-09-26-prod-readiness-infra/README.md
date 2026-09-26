# Production-readiness infrastructure — local boundary

Controlled loopback durability and fault checks for the readiness runtime.
This note is not a production-conformance claim, a public-deployment approval,
or evidence that an external payment, KYC, venue, bank, or chain effect is
exactly-once.

Protocol FSMs and `Core.execute` stay the semantic source. `readiness/` journals
committed results in a process-local file and restores them through the public
FSM `restore` methods or a fresh `Core.execute` replay. The journal is not
protocol truth. `protocolTruth`, `productionConformance`, `productionReadiness`,
and `productionEndpoint` stay false. FSM view field `durable` stays false.

Base at session start: `3b6bdd26f61bb828af3781946b63a3a3fa03187b`
(`origin/main`, including admission-hardening PR #70).

## Commands

From the repository root, Python 3.13.5:

```bash
python3 scripts/check_openapi_contract.py
python3 scripts/check_integration_gate_openapi.py --self-test
python3 -m unittest readiness.test_faults integration_gate.test_http_gate
```

Local results for this working tree, before the commit that adds this note:

- `openapi contract pin ok: commands=40 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff`
- `self-test: pass`
- `Ran 33 tests in 2.138s` — `OK`

That count is this run only. It is not CI for the commit that records this note.
Locked blobs checked before and after the edit, unchanged:

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

## What this run exercised

- Schema 1 file journal. A torn tail is discarded. A complete frame with a bad
  checksum fails closed. Version 99 is `UNSUPPORTED_SCHEMA` with no guessed
  migration. Version 1 `migrate` is the identity function.
- Settlement: a torn commit does not leave `confirmed_cash`. After a clean
  commit and one distribution, restart replays the same distribution without
  a second cash movement. A crash before the authorize record is durable
  leaves the case `INITIATED`, and the same key then authorizes once.
- Reservation: a torn hold does not occupy the slot. After one hold, restart
  keeps a single `RESERVED` slot and a second reservation id is `SLOT_OCCUPIED`.
  Two concurrent holds of the same slot leave one journal entry.
- Resale: a torn accept does not change holder or version. After one accept,
  restart keeps version 2 and a second transfer id is `ILLEGAL_TRANSITION`.
- Credit: a torn draw leaves outstanding exposure at 0. After one draw of
  80_000, restart keeps that exposure and a second draw id is `DUPLICATE_DRAW`.
- Admission: a torn consume stays `AUTHORIZED` at version 1. After one consume,
  restart stays `CONSUMED` at version 2 and another consume is `ALREADY_CONSUMED`.
- Loopback gate, default bind `127.0.0.1`: bounded in-flight returns
  `OVERLOADED`, drain keeps `/health` and refuses commands, a one-record
  journal budget refuses the next new command, and a killed process with a
  torn tail replays one `create_event` without creating a second event.
  A bad checksum or an unknown schema exits before listen.
  `0.0.0.0` is still refused.

## Hold

Not shown here: public deployment, DNS, TLS productization, a default public
bind, live PG/KYC/venue/bank adapters, chain finality, external exactly-once,
backend selection, R2, or a production-conformance claim.
