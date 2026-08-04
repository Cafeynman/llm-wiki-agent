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

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
upgrade_script="$script_dir/upgrade.sh"

if [[ ! -f "$upgrade_script" ]]; then
  echo "Upgrade script not found: $upgrade_script" >&2
  exit 1
fi

"$upgrade_script" -TargetRoot "$vault_root"
echo "Initialized package files, uv environment, and wiki structure at: $vault_root"
