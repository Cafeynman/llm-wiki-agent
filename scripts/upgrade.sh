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
inventory_path="$script_dir/package-files.txt"

if [[ ! -f "$manifest_path" ]]; then
  echo "Upgrade manifest not found: $manifest_path" >&2
  exit 1
fi
if [[ ! -f "$inventory_path" ]]; then
  echo "Package file inventory not found: $inventory_path" >&2
  exit 1
fi

inventory_paths=()
while IFS= read -r inventory_line || [[ -n "$inventory_line" ]]; do
  inventory_line="${inventory_line%$'\r'}"
  [[ -z "${inventory_line//[[:space:]]/}" ]] && continue
  [[ "$inventory_line" =~ ^[[:space:]]*# ]] && continue
  inventory_paths+=("${inventory_line//\\//}")
done < "$inventory_path"
normalize_absolute_path() {
  local path="$1"
  local index
  local part
  local stack=()
  if [[ "$path" != /* ]]; then
    path="$PWD/$path"
  fi
  local IFS='/'
  local parts=()
  read -r -a parts <<< "$path"
  for part in "${parts[@]}"; do
    case "$part" in
      ""|.) ;;
      ..)
        if [[ ${#stack[@]} -gt 0 ]]; then
          unset "stack[$((${#stack[@]} - 1))]"
        fi
        ;;
      *) stack+=("$part") ;;
    esac
  done
  if [[ ${#stack[@]} -eq 0 ]]; then
    printf "/\n"
    return
  fi
  printf "/%s" "${stack[0]}"
  for ((index = 1; index < ${#stack[@]}; index++)); do
    printf "/%s" "${stack[$index]}"
  done
  printf "\n"
}

check_target_root_path() {
  local path="$1"
  local current=""
  local segment
  local IFS='/'
  local segments=()
  read -r -a segments <<< "${path#/}"
  for segment in "${segments[@]}"; do
    [[ -z "$segment" ]] && continue
    current="$current/$segment"
    if [[ -L "$current" ]]; then
      echo "Conflict: target root path contains a symbolic link: $current" >&2
      echo "Package update stopped before writing because target paths require attention." >&2
      exit 1
    fi
    if [[ ! -e "$current" ]]; then
      return
    fi
    if [[ ! -d "$current" ]]; then
      echo "Conflict: target root path contains a non-directory component: $current" >&2
      echo "Package update stopped before writing because target paths require attention." >&2
      exit 1
    fi
  done
}

target_path="$(normalize_absolute_path "$target_root")"
check_target_root_path "$target_path"

same_root=0
if [[ "$package_root" == "$target_path" ]]; then
  same_root=1
fi

plan_rel=()
plan_source=()
plan_target=()
plan_action=()
plan_reason=()
manifest_directory_count=0
runtime_directories=(
  inbox raw/digested raw/needs-review raw/ignored raw/unsupported
  intake/tmp intake/processed intake/logs reviews/source-review reviews/reflection
  logs questions artifacts wiki/sources wiki/entities wiki/concepts wiki/claims wiki/syntheses
)
runtime_files=(
  logs/wiki.md inbox/.gitkeep wiki/home.md wiki/index.md wiki/overview.md
)
structure_conflicts=()
structure_issue_keys=()

contains_value() {
  local needle="$1"
  shift
  local value
  for value in "$@"; do
    if [[ "$value" == "$needle" ]]; then
      return 0
    fi
  done
  return 1
}

add_plan_record() {
  local relative_path="${1//\\//}"
  local source_file="$2"
  local target_file="$3"
  local action="CREATE"
  local reason=""

  if contains_value "$relative_path" "${plan_rel[@]:-}"; then
    echo "Duplicate package-managed path in manifest expansion: $relative_path" >&2
    exit 1
  fi

  if [[ "$same_root" -eq 1 ]]; then
    action="UNCHANGED"
  elif [[ -d "$target_file" ]]; then
    action="CONFLICT"
    reason="target path is a directory"
  elif [[ -f "$target_file" ]]; then
    if cmp -s "$source_file" "$target_file"; then
      action="UNCHANGED"
    else
      action="REPLACE"
    fi
  elif [[ -e "$target_file" ]]; then
    action="CONFLICT"
    reason="target path is not a regular file"
  fi

  plan_rel+=("$relative_path")
  plan_source+=("$source_file")
  plan_target+=("$target_file")
  plan_action+=("$action")
  plan_reason+=("$reason")
}

add_removal_record() {
  local relative_path="${1//\\//}"
  local target_file="$2"
  local action="UNCHANGED"
  local reason=""

  if contains_value "$relative_path" "${plan_rel[@]:-}"; then
    echo "Duplicate package-managed path in manifest expansion: $relative_path" >&2
    exit 1
  fi

  if [[ "$same_root" -eq 0 ]]; then
    if [[ -d "$target_file" ]]; then
      action="CONFLICT"
      reason="retired package path is a directory"
    elif [[ -f "$target_file" ]]; then
      action="REMOVE"
    elif [[ -e "$target_file" ]]; then
      action="CONFLICT"
      reason="retired package path is not a regular file"
    fi
  fi

  plan_rel+=("$relative_path")
  plan_source+=("")
  plan_target+=("$target_file")
  plan_action+=("$action")
  plan_reason+=("$reason")
}

add_structure_conflict() {
  local key="$1"
  local message="$2"
  if contains_value "$key" "${structure_issue_keys[@]:-}"; then
    return
  fi
  structure_issue_keys+=("$key")
  structure_conflicts+=("$message")
}

check_target_path() {
  local relative_path="${1//\\//}"
  local expected_type="$2"
  local current="$target_path"
  local display_path=""
  local index
  local is_last
  local segments=()

  case "$relative_path" in
    ""|/*|..|../*|*/../*|*/..)
      add_structure_conflict "escape:$relative_path" "$relative_path: target path escapes the workspace root"
      return
      ;;
  esac

  local IFS='/'
  read -r -a segments <<< "$relative_path"
  for ((index = 0; index < ${#segments[@]}; index++)); do
    current="$current/${segments[$index]}"
    if [[ -z "$display_path" ]]; then
      display_path="${segments[$index]}"
    else
      display_path="$display_path/${segments[$index]}"
    fi

    if [[ -L "$current" ]]; then
      add_structure_conflict "link:$display_path" "$display_path: target path is a symbolic link"
      return
    fi
    if [[ ! -e "$current" ]]; then
      return
    fi

    is_last=0
    if [[ "$index" -eq $((${#segments[@]} - 1)) ]]; then
      is_last=1
    fi
    if [[ "$is_last" -eq 0 && ! -d "$current" ]]; then
      add_structure_conflict "parent-file:$display_path" "$display_path: parent path is not a directory"
      return
    fi
    if [[ "$is_last" -eq 1 && "$expected_type" == "file" && ! -f "$current" ]]; then
      add_structure_conflict "expected-file:$display_path" "$display_path: expected a file but found another path type"
      return
    fi
    if [[ "$is_last" -eq 1 && "$expected_type" == "directory" && ! -d "$current" ]]; then
      add_structure_conflict "expected-directory:$display_path" "$display_path: expected a directory but found another path type"
      return
    fi
  done
}

while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line%$'\r'}"
  [[ -z "${line//[[:space:]]/}" ]] && continue
  [[ "$line" =~ ^[[:space:]]*# ]] && continue

  read -r kind relative_path <<< "$line"
  if [[ -z "${kind:-}" || -z "${relative_path:-}" ]]; then
    echo "Invalid manifest line: $line" >&2
    exit 1
  fi
  relative_path="${relative_path//\\//}"
  source_path="$package_root/$relative_path"

  case "$kind" in
    file)
      if [[ ! -f "$source_path" ]]; then
        echo "Manifest file entry not found in package: $relative_path" >&2
        exit 1
      fi
      add_plan_record "$relative_path" "$source_path" "$target_path/$relative_path"
      ;;
    dir)
      if [[ ! -d "$source_path" ]]; then
        echo "Manifest directory entry not found in package: $relative_path" >&2
        exit 1
      fi
      manifest_directory_count=$((manifest_directory_count + 1))
      directory_file_count=0
      for expanded in "${inventory_paths[@]:-}"; do
        [[ "$expanded" == "$relative_path/"* ]] || continue
        source_file="$package_root/$expanded"
        if [[ ! -f "$source_file" ]]; then
          echo "Inventory file entry not found in package: $expanded" >&2
          exit 1
        fi
        add_plan_record "$expanded" "$source_file" "$target_path/$expanded"
        directory_file_count=$((directory_file_count + 1))
      done
      if [[ "$directory_file_count" -eq 0 ]]; then
        echo "Manifest directory has no files in package inventory: $relative_path" >&2
        exit 1
      fi
      ;;
    remove)
      add_removal_record "$relative_path" "$target_path/$relative_path"
      ;;
    *)
      echo "Invalid manifest entry kind: $kind" >&2
      exit 1
      ;;
  esac
done < "$manifest_path"

for template_name in PROJECT.md .gitignore; do
  if [[ ! -f "$package_root/$template_name" ]]; then
    echo "Package template not found: $package_root/$template_name" >&2
    exit 1
  fi
done

for relative_path in "${plan_rel[@]}" PROJECT.md .gitignore "${runtime_files[@]}"; do
  check_target_path "$relative_path" file
done
for relative_path in "${runtime_directories[@]}" .venv; do
  check_target_path "$relative_path" directory
done

git_baseline=0
git_root=""
head_paths=()
tracked_paths=()
if [[ "$same_root" -eq 0 && -d "$target_path" ]] && command -v git >/dev/null 2>&1; then
  if git -C "$target_path" rev-parse --is-inside-work-tree >/dev/null 2>&1 &&
     git -C "$target_path" rev-parse --verify HEAD >/dev/null 2>&1; then
    git_baseline=1
    git_root="$(git -C "$target_path" rev-parse --show-toplevel)"
    while IFS= read -r head_path; do
      [[ -n "$head_path" ]] && head_paths+=("$head_path")
    done < <(git -c core.quotepath=false -C "$git_root" ls-tree -r --name-only HEAD)
    while IFS= read -r tracked_path; do
      [[ -n "$tracked_path" ]] && tracked_paths+=("$tracked_path")
    done < <(git -c core.quotepath=false -C "$git_root" ls-files)
  fi
fi

tracked_path_matches_head() {
  local git_relative="$1"
  local target_file="$2"
  local head_object
  local index_object
  local working_object

  head_object="$(git -C "$git_root" rev-parse --verify "HEAD:$git_relative" 2>/dev/null)" || return 1
  index_object="$(git -C "$git_root" rev-parse --verify ":$git_relative" 2>/dev/null)" || return 1
  [[ "$head_object" == "$index_object" ]] || return 1
  working_object="$(git -C "$git_root" hash-object --path="$git_relative" -- "$target_file" 2>/dev/null)" || return 1
  [[ "$head_object" == "$working_object" ]]
}

conflicts=("${structure_conflicts[@]}")
create_count=0
replace_count=0
remove_count=0
unchanged_count=0

for ((i = 0; i < ${#plan_rel[@]}; i++)); do
  relative_path="${plan_rel[$i]}"
  action="${plan_action[$i]}"
  target_file="${plan_target[$i]}"

  case "$action" in
    UNCHANGED)
      unchanged_count=$((unchanged_count + 1))
      continue
      ;;
    CREATE)
      create_count=$((create_count + 1))
      ;;
    REPLACE)
      replace_count=$((replace_count + 1))
      ;;
    REMOVE)
      remove_count=$((remove_count + 1))
      ;;
    CONFLICT)
      conflicts+=("$relative_path: ${plan_reason[$i]}")
      continue
      ;;
  esac

  if [[ "$git_baseline" -eq 0 ]]; then
    if [[ "$action" == "REPLACE" ]]; then
      conflicts+=("$relative_path: existing file differs and no Git baseline is available")
    elif [[ "$action" == "REMOVE" ]]; then
      conflicts+=("$relative_path: retired package file exists and no Git baseline is available")
    fi
    continue
  fi

  if [[ "$target_file" != "$git_root"/* ]]; then
    conflicts+=("$relative_path: target path is outside the Git baseline")
    continue
  fi
  git_relative="${target_file#"$git_root"/}"

  if [[ "$action" == "CREATE" ]]; then
    if contains_value "$git_relative" "${head_paths[@]:-}" ||
       contains_value "$git_relative" "${tracked_paths[@]:-}"; then
      conflicts+=("$relative_path: tracked package file is deleted in the working tree")
    fi
    continue
  fi

  if ! contains_value "$git_relative" "${head_paths[@]:-}"; then
    if [[ "$action" == "REMOVE" ]]; then
      conflicts+=("$relative_path: retired package file exists and is not tracked by the Git baseline")
    else
      conflicts+=("$relative_path: existing file differs and is not tracked by the Git baseline")
    fi
  elif ! contains_value "$git_relative" "${tracked_paths[@]:-}" ||
       ! tracked_path_matches_head "$git_relative" "$target_file"; then
    conflicts+=("$relative_path: tracked package file has uncommitted changes")
  fi
done

echo "Package file plan: create $create_count, replace $replace_count, remove $remove_count, unchanged $unchanged_count."
if [[ ${#conflicts[@]} -gt 0 ]]; then
  for conflict in "${conflicts[@]}"; do
    echo "Conflict: $conflict" >&2
  done
  echo "Package update stopped before writing because target paths require attention." >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv was not found. Install uv manually, then run this script again." >&2
  exit 1
fi
if ! (cd "$package_root" && uv lock --check --default-index https://pypi.org/simple); then
  echo "Package dependency lock is stale. Run 'uv lock --default-index https://pypi.org/simple' in the package root before upgrading." >&2
  exit 1
fi

file_count=0
removed_file_count=0
created_runtime_count=0

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

mkdir -p "$target_path"
for ((i = 0; i < ${#plan_rel[@]}; i++)); do
  action="${plan_action[$i]}"
  if [[ "$action" == "REMOVE" ]]; then
    rm -f -- "${plan_target[$i]}"
    removed_file_count=$((removed_file_count + 1))
    continue
  fi
  if [[ "$action" != "CREATE" && "$action" != "REPLACE" ]]; then
    continue
  fi
  mkdir -p "$(dirname "${plan_target[$i]}")"
  cp -f "${plan_source[$i]}" "${plan_target[$i]}"
  file_count=$((file_count + 1))
done

project_file="$target_path/PROJECT.md"
if [[ ! -e "$project_file" ]]; then
  if [[ ! -f "$package_root/PROJECT.md" ]]; then
    echo "PROJECT template not found in package: $package_root/PROJECT.md" >&2
    exit 1
  fi
  cp -f "$package_root/PROJECT.md" "$project_file"
  created_runtime_count=$((created_runtime_count + 1))
fi

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
  tr -d '\r' < "$1" | grep -Fxq "$2"
}

ensure_gitignore_line() {
  local target_file="$1"
  local line="$2"
  if gitignore_contains_line "$target_file" "$line"; then
    return
  fi
  if [[ -s "$target_file" && "$(tail -c 1 "$target_file" | wc -l)" -eq 0 ]]; then
    printf "\n" >> "$target_file"
  fi
  printf "%s\n" "$line" >> "$target_file"
}

has_tracked_wiki_runtime() {
  command -v git >/dev/null 2>&1 || return 1
  git -C "$target_path" rev-parse --is-inside-work-tree >/dev/null 2>&1 || return 1
  local tracked_path
  while IFS= read -r tracked_path; do
    [[ -z "$tracked_path" ]] && continue
    case "$tracked_path" in
      inbox/.gitkeep|*/inbox/.gitkeep) ;;
      *) return 0 ;;
    esac
  done < <(git -C "$target_path" ls-files -- wiki reviews logs questions artifacts intake/processed intake/logs raw inbox 2>/dev/null)
  return 1
}

gitignore_file="$target_path/.gitignore"
if [[ ! -e "$gitignore_file" ]]; then
  if has_tracked_wiki_runtime; then
    : > "$gitignore_file"
    for line in "${required_local_gitignore_lines[@]}"; do
      ensure_gitignore_line "$gitignore_file" "$line"
    done
    created_runtime_count=$((created_runtime_count + 1))
    echo "Created baseline-only .gitignore because durable wiki runtime files are already tracked."
  else
    if [[ ! -f "$package_root/.gitignore" ]]; then
      echo ".gitignore template not found in package: $package_root/.gitignore" >&2
      exit 1
    fi
    cp -f "$package_root/.gitignore" "$gitignore_file"
    created_runtime_count=$((created_runtime_count + 1))
    echo "Created the default private wiki runtime .gitignore policy."
  fi
else
  for line in "${required_local_gitignore_lines[@]}"; do
    ensure_gitignore_line "$gitignore_file" "$line"
  done
  echo "Preserved the target-owned .gitignore domain policy; added only secret and technical-cache rules."
fi

for dir in "${runtime_directories[@]}"; do
  ensure_directory "$target_path/$dir"
done

ensure_file "$target_path/logs/wiki.md" "# Wiki Log"$'\n'
ensure_file "$target_path/inbox/.gitkeep" ""
ensure_file "$target_path/wiki/home.md" "# Home"$'\n'
ensure_file "$target_path/wiki/index.md" "# Index"$'\n'
ensure_file "$target_path/wiki/overview.md" "# Overview"$'\n'

(
  cd "$target_path"
  uv sync --locked --default-index https://pypi.org/simple
)

echo "Upgraded package files at: $target_path"
echo "Merged manifest directories: $manifest_directory_count"
echo "Copied package files: $file_count"
echo "Removed retired package files: $removed_file_count"
echo "Created missing runtime entries: $created_runtime_count"
echo "Existing .gitignore domain rules are preserved; only secret and technical-cache baseline rules are added."
