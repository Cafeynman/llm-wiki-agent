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
same_root=0

ensure_directory() {
  mkdir -p "$1"
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

  ensure_directory "$(dirname "$target_file")"
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
  ensure_directory "$target_dir"
  target_full="$(cd "$target_dir" && pwd -P)"

  directory_count=$((directory_count + 1))

  while IFS= read -r -d '' source_file; do
    local relative_file="${source_file#"$source_full"/}"
    local target_file="$target_full/$relative_file"
    ensure_directory "$(dirname "$target_file")"
    cp -f "$source_file" "$target_file"
    file_count=$((file_count + 1))
  done < <(find "$source_full" -type f -print0)
}

if [[ ! -f "$manifest_path" ]]; then
  echo "Upgrade manifest not found: $manifest_path" >&2
  exit 1
fi

ensure_directory "$target_root"
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
