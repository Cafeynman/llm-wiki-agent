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
ensure_runtime_structure

if ! command -v uv >/dev/null 2>&1; then
  echo "uv was not found. Install uv manually, then run this script again." >&2
  exit 1
fi

(
  cd "$target_path"
  uv sync
)

echo "Upgraded package files at: $target_path"
echo "Merged directories: $directory_count"
echo "Copied files: $file_count"
echo "Created missing runtime entries: $created_runtime_count"
echo "Next project-context confirmation should ask open-ended questions for theme, goal, audience, structure, classification, naming, and project-specific rules."
echo "Use short choices only for bounded operational preferences such as MinerU, OCR, transcription, or frame OCR. Store only non-secret choices in PROJECT.md; fill only variables required by the selected profile in .env."
