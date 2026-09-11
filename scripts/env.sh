# Source this file from a Bash terminal after bootstrap.sh.
KIX_REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export KIX_REPO_ROOT
export KIX_SUI_CONFIG="$KIX_REPO_ROOT/.local/sui-config/client.yaml"
export PATH="$KIX_REPO_ROOT/.local/bin:$KIX_REPO_ROOT/.venv/bin:$PATH"
