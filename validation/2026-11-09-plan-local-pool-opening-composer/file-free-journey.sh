# Run from the repository root. Every balance below is an explicit synthetic
# example input; the console provides no suggested amount or default.
PYTHONDONTWRITEBYTECODE=1 python3 reference/token_reward/pool_console.py --guided-init <<'INPUT'
20
20
20
2
9
SUBMIT
view
credit
PROTOCOL_REVENUE
5
synthetic-source
SUBMIT
spend
PROTOCOL_REVENUE
3
synthetic-program
SUBMIT
spend
TOKEN_TREASURY_REWARD
2
synthetic-program
SUBMIT
credit
PROTOCOL_REVENUE
5
synthetic-source
SUBMIT
spend
PROTOCOL_REVENUE
3
synthetic-program
SUBMIT
view
quit
INPUT
