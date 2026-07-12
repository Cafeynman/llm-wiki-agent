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

  local template_file="$package_root/PROJECT.md"
  if [[ ! -f "$template_file" ]]; then
    echo "PROJECT template not found in package: $template_file" >&2
    exit 1
  fi

  cp -f "$template_file" "$project_file"
}

default_gitignore_block() {
  cat <<'EOF'
# Local wiki runtime content.
/inbox/*
!/inbox/.gitkeep
/raw/
/intake/
/reviews/
/logs/
/questions/
/artifacts/
/wiki/
EOF
}

private_runtime_gitignore_lines=(
  "/inbox/*"
  "!/inbox/.gitkeep"
  "/raw/"
  "/intake/"
  "/reviews/"
  "/logs/"
  "/questions/"
  "/artifacts/"
  "/wiki/"
)

versioned_runtime_gitignore_lines=(
  "/inbox/*"
  "!/inbox/.gitkeep"
  "/intake/tmp/"
)

versioned_all_intake_local_gitignore_lines=(
  "/inbox/*"
  "!/inbox/.gitkeep"
  "/intake/"
)

required_local_gitignore_lines=(
  ".env"
  "**/.env"
  ".venv/"
  "__pycache__/"
  "*.py[cod]"
  ".pytest_cache/"
  ".ruff_cache/"
  ".mypy_cache/"
  "tmp/"
  ".claude/"
  ".claudian/"
  ".codex/"
)

gitignore_contains_line() {
  local target_file="$1"
  local line="$2"
  tr -d '\r' < "$target_file" | grep -Fxq "$line"
}

gitignore_contains_all_lines() {
  local target_file="$1"
  shift

  local line
  for line in "$@"; do
    gitignore_contains_line "$target_file" "$line" || return 1
  done
  return 0
}

ensure_gitignore_trailing_newline() {
  local target_file="$1"
  if [[ -s "$target_file" && "$(tail -c 1 "$target_file" | wc -l)" -eq 0 ]]; then
    printf "\n" >> "$target_file"
  fi
}

ensure_gitignore_line() {
  local target_file="$1"
  local line="$2"
  if ! gitignore_contains_line "$target_file" "$line"; then
    ensure_gitignore_trailing_newline "$target_file"
    printf "%s\n" "$line" >> "$target_file"
  fi
}

has_wiki_runtime_gitignore_policy() {
  local target_file="$1"
  gitignore_contains_all_lines "$target_file" "${private_runtime_gitignore_lines[@]}" && return 0
  gitignore_contains_all_lines "$target_file" "${versioned_runtime_gitignore_lines[@]}" && return 0
  gitignore_contains_all_lines "$target_file" "${versioned_all_intake_local_gitignore_lines[@]}" && return 0
  return 1
}

ensure_gitignore_file() {
  local target_file="$vault_path/.gitignore"
  local template_file="$package_root/.gitignore"

  if [[ ! -e "$target_file" ]]; then
    if [[ ! -f "$template_file" ]]; then
      echo ".gitignore template not found in package: $template_file" >&2
      exit 1
    fi

    cp -f "$template_file" "$target_file"
    return
  fi

  local line
  for line in "${required_local_gitignore_lines[@]}"; do
    ensure_gitignore_line "$target_file" "$line"
  done

  if ! has_wiki_runtime_gitignore_policy "$target_file"; then
    ensure_gitignore_trailing_newline "$target_file"
    printf "\n" >> "$target_file"
    default_gitignore_block >> "$target_file"
  fi
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
  ensure_file "$vault_path/inbox/.gitkeep" ""
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
ensure_gitignore_file
ensure_runtime_structure

(
  cd "$vault_path"
  uv sync --locked --default-index https://pypi.org/simple
)

echo "Initialized package files, uv environment, and wiki structure at: $vault_path"
echo "Default .gitignore keeps wiki runtime directories local and private. Existing files are preserved; missing local baseline rules are appended, and the default runtime block is appended only when no wiki runtime policy is present. To version durable wiki content, refer to docs/gitignore-templates.md or docs/gitignore-templates.zh-CN.md."
echo "Next project-context confirmation should ask open-ended questions for theme, goal, audience, structure, classification, naming, and project-specific rules."
echo "Use short choices only for bounded operational preferences such as MinerU, OCR, transcription, or frame OCR. Store only non-secret choices in PROJECT.md; fill only variables required by the selected profile in .env."
