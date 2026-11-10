#!/usr/bin/env bash
set -eu
PYTHONDONTWRITEBYTECODE=1 python3.12 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json --mode subprocess --cleanup-timeout 1 < reference/token_reward/fixtures/reward_console_source_journey.txt
