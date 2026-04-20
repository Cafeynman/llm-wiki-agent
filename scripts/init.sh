#!/usr/bin/env bash
set -euo pipefail

vault_root="."

while [[ $# -gt 0 ]]; do
  case "$1" in
    -VaultRoot)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for -VaultRoot" >&2
        exit 1
      fi
      vault_root="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: ./scripts/init.sh [-VaultRoot PATH]" >&2
      exit 1
      ;;
  esac
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "$script_dir/.." && pwd)"

ensure_directory() {
  mkdir -p "$1"
}

ensure_file() {
  local path="$1"
  local content="$2"
  if [[ ! -e "$path" ]]; then
    ensure_directory "$(dirname "$path")"
    printf "%s" "$content" > "$path"
  fi
}

if ! command -v uv >/dev/null 2>&1; then
  echo "uv was not found. Installing uv with the official installer..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv installation did not make uv available in this shell. Install uv manually or restart the terminal, then run this script again." >&2
  exit 1
fi

ensure_directory "$vault_root"
vault_path="$(cd "$vault_root" && pwd)"

directories=(
  "inbox"
  "raw/digested"
  "raw/needs-review"
  "raw/ignored"
  "raw/unsupported"
  "intake/tmp"
  "intake/processed"
  "intake/logs"
  "reviews/source-review"
  "reviews/reflection"
  "logs"
  "questions"
  "artifacts"
  "wiki/sources"
  "wiki/entities"
  "wiki/concepts"
  "wiki/claims"
  "wiki/syntheses"
)

for dir in "${directories[@]}"; do
  ensure_directory "$vault_path/$dir"
done

ensure_file "$vault_path/logs/wiki.md" "# Wiki Log"$'\n'
ensure_file "$vault_path/wiki/home.md" "# Home"$'\n'
ensure_file "$vault_path/wiki/index.md" "# Index"$'\n'
ensure_file "$vault_path/wiki/overview.md" "# Overview"$'\n'

(
  cd "$project_root"
  uv sync
)

echo "Initialized uv environment and wiki structure at: $vault_path"
