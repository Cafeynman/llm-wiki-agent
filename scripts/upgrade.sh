#!/usr/bin/env bash
set -euo pipefail

target_root="."

while [[ $# -gt 0 ]]; do
  case "$1" in
    -TargetRoot)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for -TargetRoot" >&2
        exit 1
      fi
      target_root="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: ./scripts/upgrade.sh [-TargetRoot PATH]" >&2
      exit 1
      ;;
  esac
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
package_root="$(cd "$script_dir/.." && pwd -P)"
manifest_path="$script_dir/upgrade-manifest.txt"

file_count=0
directory_count=0
created_runtime_count=0
same_root=0

ensure_directory() {
  if [[ ! -d "$1" ]]; then
    mkdir -p "$1"
    created_runtime_count=$((created_runtime_count + 1))
  fi
}

ensure_file() {
  local path="$1"
  local content="$2"
  if [[ ! -e "$path" ]]; then
    ensure_directory "$(dirname "$path")"
    printf "%s" "$content" > "$path"
    created_runtime_count=$((created_runtime_count + 1))
  fi
}

copy_file_entry() {
  local relative_path="$1"
  local source_file="$package_root/$relative_path"
  local target_file="$target_path/$relative_path"

  if [[ ! -f "$source_file" ]]; then
    echo "Manifest file entry not found in package: $relative_path" >&2
    exit 1
  fi

  if [[ "$same_root" -eq 1 ]]; then
    return
  fi

  mkdir -p "$(dirname "$target_file")"
  cp -f "$source_file" "$target_file"
  file_count=$((file_count + 1))
}

copy_directory_entry() {
  local relative_path="$1"
  local source_dir="$package_root/$relative_path"
  local target_dir="$target_path/$relative_path"

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
  mkdir -p "$target_dir"
  target_full="$(cd "$target_dir" && pwd -P)"

  directory_count=$((directory_count + 1))

  while IFS= read -r -d '' source_file; do
    local relative_file="${source_file#"$source_full"/}"
    local target_file="$target_full/$relative_file"
    mkdir -p "$(dirname "$target_file")"
    cp -f "$source_file" "$target_file"
    file_count=$((file_count + 1))
  done < <(find "$source_full" -type f ! -name '*.pyc' ! -path '*/__pycache__/*' -print0)
}

ensure_project_file() {
  local project_file="$target_path/PROJECT.md"
  if [[ -e "$project_file" ]]; then
    return
  fi

  local template_file="$package_root/PROJECT.md"
  if [[ ! -f "$template_file" ]]; then
    echo "PROJECT template not found in package: $template_file" >&2
    exit 1
  fi

  cp -f "$template_file" "$project_file"
  created_runtime_count=$((created_runtime_count + 1))
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
  local target_file="$target_path/.gitignore"
  local template_file="$package_root/.gitignore"

  if [[ ! -e "$target_file" ]]; then
    if [[ ! -f "$template_file" ]]; then
      echo ".gitignore template not found in package: $template_file" >&2
      exit 1
    fi

    cp -f "$template_file" "$target_file"
    created_runtime_count=$((created_runtime_count + 1))
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
    created_runtime_count=$((created_runtime_count + 1))
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
    ensure_directory "$target_path/$dir"
  done

  ensure_file "$target_path/logs/wiki.md" "# Wiki Log"$'\n'
  ensure_file "$target_path/inbox/.gitkeep" ""
  ensure_file "$target_path/wiki/home.md" "# Home"$'\n'
  ensure_file "$target_path/wiki/index.md" "# Index"$'\n'
  ensure_file "$target_path/wiki/overview.md" "# Overview"$'\n'
}

if [[ ! -f "$manifest_path" ]]; then
  echo "Upgrade manifest not found: $manifest_path" >&2
  exit 1
fi

mkdir -p "$target_root"
target_path="$(cd "$target_root" && pwd -P)"
if [[ "$package_root" == "$target_path" ]]; then
  same_root=1
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

ensure_project_file
ensure_gitignore_file
ensure_runtime_structure

if ! command -v uv >/dev/null 2>&1; then
  echo "uv was not found. Install uv manually, then run this script again." >&2
  exit 1
fi

(
  cd "$target_path"
  uv sync --locked --default-index https://pypi.org/simple
)

echo "Upgraded package files at: $target_path"
echo "Merged directories: $directory_count"
echo "Copied files: $file_count"
echo "Created missing runtime entries: $created_runtime_count"
echo "Default .gitignore keeps wiki runtime directories local and private. Existing files are preserved; missing local baseline rules are appended, and the default runtime block is appended only when no wiki runtime policy is present. To version durable wiki content, refer to docs/gitignore-templates.md or docs/gitignore-templates.zh-CN.md."
echo "Next project-context confirmation should ask open-ended questions for theme, goal, audience, structure, classification, naming, and project-specific rules."
echo "Use short choices only for bounded operational preferences such as MinerU, OCR, transcription, or frame OCR. Store only non-secret choices in PROJECT.md; fill only variables required by the selected profile in .env."
