"""Foreground local command recorder; does not publish or install anything."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

folder = Path(__file__).resolve().parent
name, *command = sys.argv[1:]
start = time.monotonic()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", CARGO_NET_OFFLINE="true")
log = folder / (name + ".log")
with log.open("w") as output:
    output.write("$ " + shlex.join(command) + "\n")
    output.flush()
    result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, env=env)
    output.write("\nEXIT: %d\n" % result.returncode)
record = dict(log=log.name, command=shlex.join(command), exit=result.returncode,
              elapsed_seconds=round(time.monotonic() - start, 2))
with (folder / "commands.jsonl").open("a") as output:
    output.write(json.dumps(record) + "\n")
print(json.dumps(record), flush=True)
print("\n".join(log.read_text().splitlines()[-12:]), flush=True)
sys.exit(result.returncode)
