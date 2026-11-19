"""Run the applicable document/catalogue and KTX equivalents locally, offline.

Sequential checks only; no retry or publication.
"""
import json,os,subprocess,time
from pathlib import Path
v=Path('validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec')
env=os.environ.copy(); env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONPATH='.',CARGO_NET_OFFLINE='true')
paths=['scripts/check_docs_index.py','scripts/check_ci_test_discovery.py','scripts/check_ci_checker_wiring.py','scripts/check_openapi_contract.py','scripts/check_integration_gate_openapi.py','scripts/check_bra_evidence_map.py','scripts/check_producer_qualification_tuple.py','validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py']
commands=['python3.12 '+p+mode for p in paths for mode in ('',' --self-test')]+['python3.12 scripts/verify_runtime_architecture.py','python3.12 scripts/test_runtime_architecture.py','cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline','cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings','cargo fmt --manifest-path runtime/Cargo.toml --all -- --check']
entries=[]
for command in commands:
    log=v/f'checker-{len(entries)+1:02d}.log'; start=time.monotonic()
    with log.open('w') as out: result=subprocess.run(command,shell=True,env=env,stdout=out,stderr=subprocess.STDOUT)
    entry=dict(command=command,exit_code=result.returncode,seconds=round(time.monotonic()-start,2),log=str(log))
    entries.append(entry); (v/'checker-commands.json').write_text(json.dumps(entries,indent=2)+'\n')
    print(json.dumps(entry),flush=True)
    if result.returncode:print(log.read_text()[-4500:],flush=True)
