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
package_root="$(cd "$script_dir/.." && pwd -P)"
manifest_path="$script_dir/upgrade-manifest.txt"

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

copy_file_entry() {
  local relative_path="$1"
  local source_file="$package_root/$relative_path"
  local target_file="$vault_path/$relative_path"

  if [[ ! -f "$source_file" ]]; then
    echo "Manifest file entry not found in package: $relative_path" >&2
    exit 1
  fi

  if [[ "$same_root" -eq 1 ]]; then
    return
  fi

  ensure_directory "$(dirname "$target_file")"
  cp -f "$source_file" "$target_file"
}

copy_directory_entry() {
  local relative_path="$1"
  local source_dir="$package_root/$relative_path"
  local target_dir="$vault_path/$relative_path"

  if [[ ! -d "$source_dir" ]]; then
    echo "Manifest directory entry not found in package: $relative_path" >&2
    exit 1
  fi

  if [[ "$same_root" -eq 1 ]]; then
    return
  fi

  local source_full
  local target_full
  source_full="$(cd "$source_dir" && pwd -P)"
  ensure_directory "$target_dir"
  target_full="$(cd "$target_dir" && pwd -P)"

  while IFS= read -r -d '' source_file; do
    local relative_file="${source_file#"$source_full"/}"
    local target_file="$target_full/$relative_file"
    ensure_directory "$(dirname "$target_file")"
    cp -f "$source_file" "$target_file"
  done < <(find "$source_full" -type f ! -name '*.pyc' ! -path '*/__pycache__/*' -print0)
}

install_package_files() {
  if [[ ! -f "$manifest_path" ]]; then
    echo "Upgrade manifest not found: $manifest_path" >&2
    exit 1
  fi

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "${line//[[:space:]]/}" ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue

    read -r kind relative_path <<< "$line"
    if [[ -z "${kind:-}" || -z "${relative_path:-}" ]]; then
      echo "Invalid manifest line: $line" >&2
      exit 1
    fi

    case "$kind" in
      file)
        copy_file_entry "$relative_path"
        ;;
      dir)
        copy_directory_entry "$relative_path"
        ;;
      *)
        echo "Invalid manifest entry kind: $kind" >&2
        exit 1
        ;;
    esac
  done < "$manifest_path"
}

ensure_project_file() {
  local project_file="$vault_path/PROJECT.md"
  if [[ -e "$project_file" ]]; then
    return
  fi

  cat > "$project_file" <<EOF
# Project Context

This file records the current workspace's configurable project context, including project-specific wiki structure requirements, classification preferences, naming preferences, and project-specific rules. The agent should complete it during the first project-context initialization conversation and update it when the project subject changes.

Fields are optional unless required for the current task. Leave a field blank when the project has no specific preference; blank fields mean "not specified," not "to be invented."

## Workspace Paths

- Vault root: $vault_path
- Package root: $vault_path

## Context

- Theme:
- Goal:
- Audience:
- Scope:
- Preferred terms:
- Wiki structure requirements:
- Classification preferences:
- Naming preferences:
- Project-specific rules:
- Constraints:
- Open questions:

## Source Extraction Preferences

- Preferences status: unconfirmed
- Default provider for document: markitdown
- Alternative provider for document: mineru
- MinerU API key status: unconfirmed
- Prefer MinerU when available: unconfirmed
- PDF preflight policy: lightweight
- Default provider for webpage: defuddle
- Image extraction policy: ask-before-ocr
- Audio extraction policy: ask-before-transcription
- Video extraction policy: ask-before-transcription-or-frame-ocr
- Unsupported source kinds:
- Provider-specific preferences: non-secret provider choices only; private endpoints and secret values belong in the project-root .env
EOF
}

ensure_runtime_structure() {
  local directories=(
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
vault_path="$(cd "$vault_root" && pwd -P)"
same_root=0
if [[ "$package_root" == "$vault_path" ]]; then
  same_root=1
fi

install_package_files
ensure_project_file
ensure_runtime_structure

(
  cd "$vault_path"
  uv sync
)

echo "Initialized package files, uv environment, and wiki structure at: $vault_path"
echo "Next project-context confirmation should ask whether to configure MinerU and whether to prefer MinerU when available. Store only non-secret choices in PROJECT.md; put any MinerU token in .env as MINERU_TOKEN."
