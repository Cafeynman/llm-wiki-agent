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

runtime_os="$(uname -s 2>/dev/null || true)"
case "$runtime_os" in
  MINGW*|MSYS*|CYGWIN*)
    echo "upgrade.sh supports macOS and Linux only; use scripts/upgrade.ps1 on Windows." >&2
    exit 1
    ;;
esac

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
package_root="$(cd "$script_dir/.." && pwd -P)"
manifest_path="$script_dir/upgrade-manifest.txt"
inventory_path="$script_dir/package-files.txt"
complete_inventory_marker="# inventory-format: complete"

if [[ ! -f "$manifest_path" ]]; then
  echo "Upgrade manifest not found: $manifest_path" >&2
  exit 1
fi
if [[ ! -f "$inventory_path" ]]; then
  echo "Package file inventory not found: $inventory_path" >&2
  exit 1
fi

normalize_absolute_path() {
  local path="$1"
  local index
  local part
  local stack=()
  case "$path" in
    [[:alpha:]]:[\\/]* )
      echo "Windows drive-style paths are not supported by upgrade.sh; use scripts/upgrade.ps1 on Windows." >&2
      exit 1
      ;;
  esac
  if [[ "$path" != /* ]]; then
    path="$PWD/$path"
  fi
  local IFS='/'
  local parts=()
  read -r -a parts <<< "$path"
  for ((index = 0; index < ${#parts[@]}; index++)); do
    part="${parts[$index]}"
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
  local index
  local IFS='/'
  local segments=()
  read -r -a segments <<< "${path#/}"
  for ((index = 0; index < ${#segments[@]}; index++)); do
    segment="${segments[$index]}"
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
plan_metadata_order=()
plan_seen_keys=()
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

trim_text() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  REPLY="$value"
}

normalize_package_path() {
  local raw_path="$1"
  local context="$2"
  local relative_path="${raw_path//\\//}"
  local segment
  local index
  trim_text "$relative_path"
  relative_path="$REPLY"
  case "$relative_path" in
    ""|/*|*/|*//*|*:*)
      echo "$context contains an invalid package path: $raw_path" >&2
      exit 1
      ;;
  esac
  local IFS='/'
  local segments=()
  read -r -a segments <<< "$relative_path"
  for ((index = 0; index < ${#segments[@]}; index++)); do
    segment="${segments[$index]}"
    if [[ -z "$segment" || "$segment" == "." || "$segment" == ".." ]]; then
      echo "$context contains an invalid package path: $raw_path" >&2
      exit 1
    fi
  done
  REPLY="$relative_path"
}

active_owners=()
active_keys=()
active_paths=()
active_sources=()
removed_owners=()
removed_keys=()
removed_paths=()
new_directory_count=0
old_directory_count=0
new_inventory_mode="none"
old_inventory_mode="none"

lowercase_text() {
  local value="$1"
  value="${value//A/a}"
  value="${value//B/b}"
  value="${value//C/c}"
  value="${value//D/d}"
  value="${value//E/e}"
  value="${value//F/f}"
  value="${value//G/g}"
  value="${value//H/h}"
  value="${value//I/i}"
  value="${value//J/j}"
  value="${value//K/k}"
  value="${value//L/l}"
  value="${value//M/m}"
  value="${value//N/n}"
  value="${value//O/o}"
  value="${value//P/p}"
  value="${value//Q/q}"
  value="${value//R/r}"
  value="${value//S/s}"
  value="${value//T/t}"
  value="${value//U/u}"
  value="${value//V/v}"
  value="${value//W/w}"
  value="${value//X/x}"
  value="${value//Y/y}"
  value="${value//Z/z}"
  REPLY="$value"
}

find_active() {
  local owner="$1"
  local key="$2"
  local index
  FOUND_INDEX=-1
  for ((index = 0; index < ${#active_keys[@]}; index++)); do
    if [[ "${active_owners[$index]}" == "$owner" && "${active_keys[$index]}" == "$key" ]]; then
      FOUND_INDEX="$index"
      return 0
    fi
  done
  return 0
}

find_removed() {
  local owner="$1"
  local key="$2"
  local index
  FOUND_INDEX=-1
  for ((index = 0; index < ${#removed_keys[@]}; index++)); do
    if [[ "${removed_owners[$index]}" == "$owner" && "${removed_keys[$index]}" == "$key" ]]; then
      FOUND_INDEX="$index"
      return 0
    fi
  done
  return 0
}

add_active() {
  active_owners+=("$1")
  active_keys+=("$2")
  active_paths+=("$3")
  active_sources+=("$4")
}

add_removed() {
  removed_owners+=("$1")
  removed_keys+=("$2")
  removed_paths+=("$3")
}

list_active_keys() {
  local owner="$1"
  local index
  for ((index = 0; index < ${#active_keys[@]}; index++)); do
    if [[ "${active_owners[$index]}" == "$owner" ]]; then
      printf '%s\n' "${active_keys[$index]}"
    fi
  done
}

list_removed_keys() {
  local owner="$1"
  local index
  for ((index = 0; index < ${#removed_keys[@]}; index++)); do
    if [[ "${removed_owners[$index]}" == "$owner" ]]; then
      printf '%s\n' "${removed_keys[$index]}"
    fi
  done
}

assert_package_source_path_safe() {
  local root_path="$1"
  local relative_path="$2"
  local expected_type="$3"
  local context="$4"
  local current="$root_path"
  local index
  local segments=()
  local IFS='/'
  read -r -a segments <<< "$relative_path"
  for ((index = 0; index < ${#segments[@]}; index++)); do
    current="$current/${segments[$index]}"
    if [[ -L "$current" ]]; then
      echo "$context contains a symbolic link: $relative_path" >&2
      exit 1
    fi
    if [[ ! -e "$current" ]]; then
      echo "$context not found: $relative_path" >&2
      exit 1
    fi
    if [[ "$index" -lt $((${#segments[@]} - 1)) && ! -d "$current" ]]; then
      echo "$context contains a non-directory ancestor: $relative_path" >&2
      exit 1
    fi
    if [[ "$index" -eq $((${#segments[@]} - 1)) && "$expected_type" == "file" && ! -f "$current" ]]; then
      echo "$context is not a regular file: $relative_path" >&2
      exit 1
    fi
    if [[ "$index" -eq $((${#segments[@]} - 1)) && "$expected_type" == "directory" && ! -d "$current" ]]; then
      echo "$context is not a directory: $relative_path" >&2
      exit 1
    fi
  done
}

read_ownership_metadata() {
  local root_path="$1"
  local metadata_manifest="$2"
  local metadata_inventory="$3"
  local require_source_files="$4"
  local owner="$5"
  local label="$6"
  local inventory_mode="directories"
  local manifest_inventory_mode="directories"
  local inventory_directive_seen=0
  local ownership_entry_seen=0
  local complete_inventory_marker_seen=0
  local manifest_direct_keys=()
  local manifest_direct_paths=()
  local manifest_directory_keys=()
  local manifest_directory_paths=()
  local manifest_removed_keys=()
  local manifest_removed_paths=()
  local manifest_explicit_keys=()
  local inventory_states=()
  local inventory_keys=()
  local inventory_paths=()
  local consumed_inventory_keys=()
  local line
  local kind
  local raw_relative
  local relative_path
  local key
  local index
  local manifest_index
  local inventory_index
  local active_index
  local removed_index
  local found
  local declared_active
  local declared_removed
  local consumed_found

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    line="${line#$'\xEF\xBB\xBF'}"
    trim_text "$line"
    line="$REPLY"
    if [[ "$line" == "$complete_inventory_marker" ]]; then
      if [[ "$complete_inventory_marker_seen" -eq 1 ]]; then
        echo "$label inventory contains a duplicate complete-format marker." >&2
        exit 1
      fi
      complete_inventory_marker_seen=1
    fi
  done < "$metadata_inventory"

  if [[ -n "$metadata_manifest" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%$'\r'}"
      line="${line#$'\xEF\xBB\xBF'}"
      trim_text "$line"
      line="$REPLY"
      [[ -z "$line" || "$line" == \#* ]] && continue
      if [[ "$line" != *[[:space:]]* ]]; then
        echo "Invalid $label manifest line: $line" >&2
        exit 1
      fi
      kind="${line%%[[:space:]]*}"
      raw_relative="${line#"$kind"}"
      trim_text "$raw_relative"
      raw_relative="$REPLY"

      if [[ "$kind" == "inventory" ]]; then
        if [[ "$raw_relative" != "all" ]]; then
          echo "Invalid $label inventory directive: $line" >&2
          exit 1
        fi
        if [[ "$inventory_directive_seen" -eq 1 || "$ownership_entry_seen" -eq 1 ]]; then
          echo "$label manifest must declare 'inventory all' exactly once before ownership entries." >&2
          exit 1
        fi
        inventory_directive_seen=1
        inventory_mode="all"
        continue
      fi

      case "$kind" in
        file|dir|remove) ;;
        *)
          echo "Invalid $label manifest entry kind: $kind" >&2
          exit 1
          ;;
      esac

      normalize_package_path "$raw_relative" "$label manifest"
      relative_path="$REPLY"
      lowercase_text "$relative_path"
      key="$REPLY"
      ownership_entry_seen=1

      if [[ "$kind" == "file" || "$kind" == "remove" ]]; then
        for ((index = 0; index < ${#manifest_explicit_keys[@]}; index++)); do
          if [[ "${manifest_explicit_keys[$index]}" == "$key" ]]; then
            echo "$label manifest contains a duplicate package path: $relative_path" >&2
            exit 1
          fi
        done
        manifest_explicit_keys+=("$key")
      fi

      case "$kind" in
        file)
          manifest_direct_keys+=("$key")
          manifest_direct_paths+=("$relative_path")
          ;;
        dir)
          for ((index = 0; index < ${#manifest_directory_keys[@]}; index++)); do
            if [[ "${manifest_directory_keys[$index]}" == "$key" ]]; then
              echo "$label manifest contains a duplicate directory entry: $relative_path" >&2
              exit 1
            fi
          done
          manifest_directory_keys+=("$key")
          manifest_directory_paths+=("$relative_path")
          ;;
        remove)
          if [[ "$key" == "scripts/upgrade-manifest.txt" || "$key" == "scripts/package-files.txt" ]]; then
            echo "$label manifest cannot retire ownership metadata: $relative_path" >&2
            exit 1
          fi
          manifest_removed_keys+=("$key")
          manifest_removed_paths+=("$relative_path")
          ;;
      esac
    done < "$metadata_manifest"
  fi

  manifest_inventory_mode="$inventory_mode"
  if [[ "$require_source_files" -eq 1 && "$manifest_inventory_mode" != "all" ]]; then
    echo "$label manifest must declare 'inventory all' before ownership entries." >&2
    exit 1
  fi
  if [[ "$require_source_files" -eq 1 && "$complete_inventory_marker_seen" -eq 0 ]]; then
    echo "$label inventory must declare '$complete_inventory_marker'." >&2
    exit 1
  fi
  if [[ -z "$metadata_manifest" && "$complete_inventory_marker_seen" -eq 0 ]]; then
    echo "$label ownership metadata is incomplete; a standalone inventory must declare '$complete_inventory_marker'." >&2
    exit 1
  fi
  if [[ "$complete_inventory_marker_seen" -eq 1 ]]; then
    inventory_mode="all"
  elif [[ "$manifest_inventory_mode" == "all" ]]; then
    echo "$label complete manifest is paired with an unmarked inventory; restore the matching ownership metadata pair and rerun." >&2
    exit 1
  fi

  if [[ "$owner" == "new" ]]; then
    new_directory_count="${#manifest_directory_paths[@]}"
    new_inventory_mode="$inventory_mode"
  else
    old_directory_count="${#manifest_directory_paths[@]}"
    old_inventory_mode="$inventory_mode"
  fi

  if [[ "$inventory_mode" == "directories" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%$'\r'}"
      line="${line#$'\xEF\xBB\xBF'}"
      trim_text "$line"
      line="$REPLY"
      [[ -z "$line" || "$line" == \#* ]] && continue
      normalize_package_path "$line" "$label inventory"
      relative_path="$REPLY"
      lowercase_text "$relative_path"
      key="$REPLY"
      for ((index = 0; index < ${#inventory_keys[@]}; index++)); do
        if [[ "${inventory_keys[$index]}" == "$key" ]]; then
          echo "$label inventory contains a duplicate package path: $relative_path" >&2
          exit 1
        fi
      done
      inventory_keys+=("$key")
      inventory_paths+=("$relative_path")
    done < "$metadata_inventory"

    for ((manifest_index = 0; manifest_index < ${#manifest_direct_paths[@]}; manifest_index++)); do
      relative_path="${manifest_direct_paths[$manifest_index]}"
      key="${manifest_direct_keys[$manifest_index]}"
      add_active "$owner" "$key" "$relative_path" "$root_path/$relative_path"
    done

    for ((manifest_index = 0; manifest_index < ${#manifest_directory_paths[@]}; manifest_index++)); do
      local directory_path="${manifest_directory_paths[$manifest_index]}"
      local expanded_count=0
      for ((inventory_index = 0; inventory_index < ${#inventory_paths[@]}; inventory_index++)); do
        relative_path="${inventory_paths[$inventory_index]}"
        [[ "$relative_path" == "$directory_path/"* ]] || continue
        key="${inventory_keys[$inventory_index]}"
        find_active "$owner" "$key"
        active_index="$FOUND_INDEX"
        find_removed "$owner" "$key"
        removed_index="$FOUND_INDEX"
        if [[ "$active_index" -ge 0 || "$removed_index" -ge 0 ]]; then
          echo "$label manifest contains a duplicate package path: $relative_path" >&2
          exit 1
        fi
        add_active "$owner" "$key" "$relative_path" "$root_path/$relative_path"
        consumed_inventory_keys+=("$key")
        expanded_count=$((expanded_count + 1))
      done
      if [[ "$expanded_count" -eq 0 ]]; then
        echo "$label manifest directory has no files in its inventory: $directory_path" >&2
        exit 1
      fi
    done

    for ((manifest_index = 0; manifest_index < ${#manifest_removed_paths[@]}; manifest_index++)); do
      relative_path="${manifest_removed_paths[$manifest_index]}"
      key="${manifest_removed_keys[$manifest_index]}"
      find_active "$owner" "$key"
      active_index="$FOUND_INDEX"
      find_removed "$owner" "$key"
      removed_index="$FOUND_INDEX"
      if [[ "$active_index" -ge 0 || "$removed_index" -ge 0 ]]; then
        echo "$label manifest contains a duplicate package path: $relative_path" >&2
        exit 1
      fi
      add_removed "$owner" "$key" "$relative_path"
    done

    for ((inventory_index = 0; inventory_index < ${#inventory_paths[@]}; inventory_index++)); do
      relative_path="${inventory_paths[$inventory_index]}"
      key="${inventory_keys[$inventory_index]}"
      consumed_found=0
      for ((index = 0; index < ${#consumed_inventory_keys[@]}; index++)); do
        if [[ "${consumed_inventory_keys[$index]}" == "$key" ]]; then
          consumed_found=1
          break
        fi
      done
      if [[ "$consumed_found" -eq 0 ]]; then
        echo "$label inventory path is not owned by a manifest directory: $relative_path" >&2
        exit 1
      fi
    done
    return
  fi

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    line="${line#$'\xEF\xBB\xBF'}"
    trim_text "$line"
    line="$REPLY"
    [[ -z "$line" || "$line" == \#* ]] && continue
    if [[ "$line" != *[[:space:]]* ]]; then
      echo "Invalid $label complete inventory line: $line" >&2
      exit 1
    fi
    local inventory_state="${line%%[[:space:]]*}"
    raw_relative="${line#"$inventory_state"}"
    trim_text "$raw_relative"
    raw_relative="$REPLY"
    if [[ "$inventory_state" != "active" && "$inventory_state" != "remove" ]]; then
      echo "Invalid $label complete inventory line: $line" >&2
      exit 1
    fi
    normalize_package_path "$raw_relative" "$label inventory"
    relative_path="$REPLY"
    lowercase_text "$relative_path"
    key="$REPLY"
    for ((index = 0; index < ${#inventory_keys[@]}; index++)); do
      if [[ "${inventory_keys[$index]}" == "$key" ]]; then
        echo "$label inventory contains a duplicate package path: $relative_path" >&2
        exit 1
      fi
    done
    inventory_states+=("$inventory_state")
    inventory_keys+=("$key")
    inventory_paths+=("$relative_path")
  done < "$metadata_inventory"

  for ((inventory_index = 0; inventory_index < ${#inventory_paths[@]}; inventory_index++)); do
    local inventory_state="${inventory_states[$inventory_index]}"
    relative_path="${inventory_paths[$inventory_index]}"
    key="${inventory_keys[$inventory_index]}"
    declared_active=0
    for ((index = 0; index < ${#manifest_direct_keys[@]}; index++)); do
      if [[ "${manifest_direct_keys[$index]}" == "$key" ]]; then
        declared_active=1
        break
      fi
    done
    if [[ "$declared_active" -eq 0 ]]; then
      for ((index = 0; index < ${#manifest_directory_paths[@]}; index++)); do
        if [[ "$relative_path" == "${manifest_directory_paths[$index]}/"* ]]; then
          declared_active=1
          break
        fi
      done
    fi
    declared_removed=0
    for ((index = 0; index < ${#manifest_removed_keys[@]}; index++)); do
      if [[ "${manifest_removed_keys[$index]}" == "$key" ]]; then
        declared_removed=1
        break
      fi
    done

    if [[ "$require_source_files" -eq 1 ]]; then
      if [[ "$declared_active" -eq 0 && "$declared_removed" -eq 0 ]]; then
        echo "$label inventory path is not classified by the manifest: $relative_path" >&2
        exit 1
      fi
      if [[ "$inventory_state" == "active" && ( "$declared_active" -eq 0 || "$declared_removed" -eq 1 ) ]]; then
        echo "$label inventory classification does not match the manifest: active $relative_path" >&2
        exit 1
      fi
      if [[ "$inventory_state" == "remove" && "$declared_removed" -eq 0 ]]; then
        echo "$label inventory classification does not match the manifest: remove $relative_path" >&2
        exit 1
      fi
    fi

    if [[ "$inventory_state" == "active" ]]; then
      if [[ "$require_source_files" -eq 1 ]]; then
        assert_package_source_path_safe "$root_path" "$relative_path" file "$label active inventory entry"
      fi
      add_active "$owner" "$key" "$relative_path" "$root_path/$relative_path"
    else
      add_removed "$owner" "$key" "$relative_path"
    fi
  done

  if [[ "$require_source_files" -eq 1 ]]; then
    for ((manifest_index = 0; manifest_index < ${#manifest_direct_paths[@]}; manifest_index++)); do
      relative_path="${manifest_direct_paths[$manifest_index]}"
      key="${manifest_direct_keys[$manifest_index]}"
      found=0
      for ((inventory_index = 0; inventory_index < ${#inventory_keys[@]}; inventory_index++)); do
        if [[ "${inventory_keys[$inventory_index]}" == "$key" && "${inventory_states[$inventory_index]}" == "active" ]]; then
          found=1
          break
        fi
      done
      if [[ "$found" -eq 0 ]]; then
        echo "$label inventory is missing active manifest path: $relative_path" >&2
        exit 1
      fi
    done

    for ((manifest_index = 0; manifest_index < ${#manifest_removed_paths[@]}; manifest_index++)); do
      relative_path="${manifest_removed_paths[$manifest_index]}"
      key="${manifest_removed_keys[$manifest_index]}"
      found=0
      for ((inventory_index = 0; inventory_index < ${#inventory_keys[@]}; inventory_index++)); do
        if [[ "${inventory_keys[$inventory_index]}" == "$key" && "${inventory_states[$inventory_index]}" == "remove" ]]; then
          found=1
          break
        fi
      done
      if [[ "$found" -eq 0 ]]; then
        echo "$label inventory is missing retired manifest path: $relative_path" >&2
        exit 1
      fi
    done

    for ((manifest_index = 0; manifest_index < ${#manifest_directory_paths[@]}; manifest_index++)); do
      local directory_path="${manifest_directory_paths[$manifest_index]}"
      found=0
      for ((inventory_index = 0; inventory_index < ${#inventory_paths[@]}; inventory_index++)); do
        if [[ "${inventory_states[$inventory_index]}" == "active" && "${inventory_paths[$inventory_index]}" == "$directory_path/"* ]]; then
          found=1
          break
        fi
      done
      if [[ "$found" -eq 0 ]]; then
        echo "$label manifest directory has no active files in its inventory: $directory_path" >&2
        exit 1
      fi
      assert_package_source_path_safe "$root_path" "$directory_path" directory "$label manifest directory entry"
    done
  fi
}

check_ownership_metadata_path_safe() {
  local relative_path="$1"
  local current="$target_path"
  local segment
  local index
  local IFS='/'
  local segments=()
  read -r -a segments <<< "$relative_path"
  for ((index = 0; index < ${#segments[@]}; index++)); do
    segment="${segments[$index]}"
    current="$current/$segment"
    if [[ -L "$current" ]]; then
      echo "Old package ownership metadata path is a symbolic link: $relative_path" >&2
      exit 1
    fi
    [[ -e "$current" ]] || return 0
    if [[ "$index" -lt $((${#segments[@]} - 1)) && ! -d "$current" ]]; then
      echo "Old package ownership metadata parent is not a directory: $relative_path" >&2
      exit 1
    fi
    if [[ "$index" -eq $((${#segments[@]} - 1)) && ! -f "$current" ]]; then
      echo "Old package ownership metadata path is not a regular file: $relative_path" >&2
      exit 1
    fi
  done
}

assert_package_source_path_safe "$package_root" "scripts/upgrade-manifest.txt" file "Upgrade manifest"
assert_package_source_path_safe "$package_root" "scripts/package-files.txt" file "Package file inventory"
read_ownership_metadata "$package_root" "$manifest_path" "$inventory_path" 1 new "New package"
manifest_directory_count="$new_directory_count"

old_manifest="$target_path/scripts/upgrade-manifest.txt"
old_inventory="$target_path/scripts/package-files.txt"
check_ownership_metadata_path_safe "scripts/upgrade-manifest.txt"
check_ownership_metadata_path_safe "scripts/package-files.txt"
old_available=0
if [[ -f "$old_manifest" && -f "$old_inventory" ]]; then
  old_available=1
  read_ownership_metadata "$target_path" "$old_manifest" "$old_inventory" 0 old "Old package"
elif [[ ! -e "$old_manifest" && -f "$old_inventory" ]]; then
  old_available=1
  read_ownership_metadata "$target_path" "" "$old_inventory" 0 old "Old package"
elif [[ -e "$old_manifest" || -e "$old_inventory" ]]; then
  echo "Old package ownership metadata is incomplete; both scripts/upgrade-manifest.txt and scripts/package-files.txt are required." >&2
  exit 1
fi

safe_target_file_state() {
  local relative_path="$1"
  local current="$target_path"
  local display_path=""
  local segment
  local index
  local IFS='/'
  local segments=()
  read -r -a segments <<< "$relative_path"
  TARGET_STATE="MISSING"
  TARGET_REASON=""
  for ((index = 0; index < ${#segments[@]}; index++)); do
    segment="${segments[$index]}"
    current="$current/$segment"
    display_path="${display_path:+$display_path/}$segment"
    if [[ -L "$current" ]]; then
      TARGET_STATE="CONFLICT"
      TARGET_REASON="$display_path is a symbolic link"
      return
    fi
    [[ -e "$current" ]] || return 0
    if [[ "$index" -lt $((${#segments[@]} - 1)) && ! -d "$current" ]]; then
      TARGET_STATE="CONFLICT"
      TARGET_REASON="$display_path is not a directory"
      return
    fi
    if [[ "$index" -eq $((${#segments[@]} - 1)) ]]; then
      if [[ -f "$current" ]]; then
        TARGET_STATE="FILE"
      elif [[ -d "$current" ]]; then
        TARGET_STATE="CONFLICT"
        TARGET_REASON="target path is a directory"
      else
        TARGET_STATE="CONFLICT"
        TARGET_REASON="target path is not a regular file"
      fi
      return
    fi
  done
}

add_plan_record() {
  local relative_path="$1"
  local source_file="$2"
  local action="$3"
  local reason="$4"
  lowercase_text "$relative_path"
  local key="$REPLY"
  local index
  for ((index = 0; index < ${#plan_seen_keys[@]}; index++)); do
    if [[ "${plan_seen_keys[$index]}" == "$key" ]]; then
      echo "Duplicate package path while building the ownership plan: $relative_path" >&2
      exit 1
    fi
  done
  plan_seen_keys+=("$key")
  local metadata_order=0
  [[ "$key" == "scripts/upgrade-manifest.txt" ]] && metadata_order=1
  [[ "$key" == "scripts/package-files.txt" ]] && metadata_order=2
  plan_rel+=("$relative_path")
  plan_source+=("$source_file")
  plan_target+=("$target_path/$relative_path")
  plan_action+=("$action")
  plan_reason+=("$reason")
  plan_metadata_order+=("$metadata_order")
}

while IFS= read -r key; do
  [[ -z "$key" ]] && continue
  find_active new "$key"
  new_index="$FOUND_INDEX"
  relative_path="${active_paths[$new_index]}"
  source_file="${active_sources[$new_index]}"
  target_file="$target_path/$relative_path"
  action="CREATE"
  reason=""
  safe_target_file_state "$relative_path"
  if [[ "$same_root" -eq 1 ]]; then
    action="UNCHANGED"
  elif [[ "$TARGET_STATE" == "CONFLICT" ]]; then
    action="CONFLICT"
    reason="$TARGET_REASON"
  elif [[ "$TARGET_STATE" == "FILE" ]]; then
    if cmp -s "$source_file" "$target_file"; then
      action="UNCHANGED"
    elif [[ "$old_available" -eq 1 ]]; then
      find_active old "$key"
      if [[ "$FOUND_INDEX" -ge 0 ]]; then
        action="REPLACE"
      else
        action="CONFLICT"
        reason="new package-owned path already exists with different content"
      fi
    else
      action="CONFLICT"
      reason="new package-owned path already exists with different content"
    fi
  fi
  add_plan_record "$relative_path" "$source_file" "$action" "$reason"
done < <(list_active_keys new | LC_ALL=C sort)

if [[ "$old_available" -eq 1 ]]; then
  while IFS= read -r key; do
    [[ -z "$key" ]] && continue
    find_active new "$key"
    [[ "$FOUND_INDEX" -ge 0 ]] && continue
    find_active old "$key"
    old_index="$FOUND_INDEX"
    relative_path="${active_paths[$old_index]}"
    find_removed new "$key"
    if [[ "$FOUND_INDEX" -lt 0 ]]; then
      add_plan_record "$relative_path" "" "CONFLICT" "old package-owned path is absent from the new manifest without an explicit remove entry"
      continue
    fi
    action="UNCHANGED"
    reason=""
    safe_target_file_state "$relative_path"
    if [[ "$same_root" -eq 0 ]]; then
      if [[ "$TARGET_STATE" == "CONFLICT" ]]; then
        action="CONFLICT"
        reason="$TARGET_REASON"
      elif [[ "$TARGET_STATE" == "FILE" ]]; then
        action="REMOVE"
      fi
    fi
    add_plan_record "$relative_path" "" "$action" "$reason"
  done < <(list_active_keys old | LC_ALL=C sort)
fi

while IFS= read -r key; do
  [[ -z "$key" ]] && continue
  seen_in_plan=0
  for ((i = 0; i < ${#plan_seen_keys[@]}; i++)); do
    if [[ "${plan_seen_keys[$i]}" == "$key" ]]; then
      seen_in_plan=1
      break
    fi
  done
  [[ "$seen_in_plan" -eq 1 ]] && continue
  find_removed new "$key"
  removed_index="$FOUND_INDEX"
  relative_path="${removed_paths[$removed_index]}"
  action="UNCHANGED"
  reason=""
  safe_target_file_state "$relative_path"
  if [[ "$same_root" -eq 0 ]]; then
    if [[ "$TARGET_STATE" == "CONFLICT" ]]; then
      action="CONFLICT"
      reason="$TARGET_REASON"
    elif [[ "$TARGET_STATE" == "FILE" ]]; then
      if [[ "$old_available" -eq 1 ]]; then
        find_removed old "$key"
      else
        FOUND_INDEX=-1
      fi
      if [[ "$FOUND_INDEX" -ge 0 ]]; then
        action="REMOVE"
      else
        action="CONFLICT"
        reason="retired package path exists without prior active or retired package ownership"
      fi
    fi
  fi
  add_plan_record "$relative_path" "" "$action" "$reason"
done < <(list_removed_keys new | LC_ALL=C sort)

add_structure_conflict() {
  local key="$1"
  local message="$2"
  local index
  for ((index = 0; index < ${#structure_issue_keys[@]}; index++)); do
    if [[ "${structure_issue_keys[$index]}" == "$key" ]]; then
      return
    fi
  done
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

for template_name in PROJECT.md .gitignore; do
  assert_package_source_path_safe "$package_root" "$template_name" file "Package template"
done

for ((i = 0; i < ${#plan_rel[@]}; i++)); do
  check_target_path "${plan_rel[$i]}" file
done
for relative_path in PROJECT.md .gitignore "${runtime_files[@]}"; do
  check_target_path "$relative_path" file
done
for relative_path in "${runtime_directories[@]}" .venv; do
  check_target_path "$relative_path" directory
done

conflicts=()
for ((i = 0; i < ${#structure_conflicts[@]}; i++)); do
  conflicts+=("${structure_conflicts[$i]}")
done
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
      ;;
  esac
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
  [[ "${plan_metadata_order[$i]}" -eq 0 ]] || continue
  action="${plan_action[$i]}"
  if [[ "$action" == "REMOVE" ]]; then
    rm -f "${plan_target[$i]}"
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
  ".obsidian/"
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

gitignore_file="$target_path/.gitignore"
if [[ ! -e "$gitignore_file" ]]; then
  if [[ ! -f "$package_root/.gitignore" ]]; then
    echo ".gitignore template not found in package: $package_root/.gitignore" >&2
    exit 1
  fi
  cp -f "$package_root/.gitignore" "$gitignore_file"
  created_runtime_count=$((created_runtime_count + 1))
  echo "Created the default private wiki runtime .gitignore policy."
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

if ! (
  cd "$target_path"
  uv sync --locked --default-index https://pypi.org/simple
); then
  echo "Package dependency sync failed; ownership metadata was not advanced." >&2
  exit 1
fi

commit_metadata_file() {
  local source_file="$1"
  local target_file="$2"
  local target_directory
  local target_name
  local temporary_file
  target_directory="$(dirname "$target_file")"
  target_name="$(basename "$target_file")"
  mkdir -p "$target_directory"
  temporary_file="$(mktemp "$target_directory/.$target_name.upgrade.XXXXXX")"
  if ! cp -f "$source_file" "$temporary_file"; then
    rm -f "$temporary_file"
    echo "Failed to stage package ownership metadata: $source_file" >&2
    return 1
  fi
  if ! chmod 644 "$temporary_file"; then
    rm -f "$temporary_file"
    echo "Failed to set package ownership metadata permissions: $temporary_file" >&2
    return 1
  fi
  if ! mv -f "$temporary_file" "$target_file"; then
    rm -f "$temporary_file"
    echo "Failed to commit package ownership metadata: $target_file" >&2
    return 1
  fi
  file_count=$((file_count + 1))
}

commit_inventory_checkpoint() {
  local target_file="$old_inventory"
  local target_directory
  local target_name
  local temporary_file
  local index
  target_directory="$(dirname "$target_file")"
  target_name="$(basename "$target_file")"
  mkdir -p "$target_directory"
  temporary_file="$(mktemp "$target_directory/.$target_name.upgrade.XXXXXX")"
  if ! {
    printf '%s\n' \
      '# Complete package-ownership activation inventory for upgrade-manifest.txt.' \
      "$complete_inventory_marker" \
      '# Every active file and retired path is listed; the final inventory is committed last.' \
      '# Format: active <path> or remove <path>.'
    if [[ "$old_inventory_mode" == "none" ]]; then
      printf 'active %s\n' 'scripts/package-files.txt'
    fi
    for ((index = 0; index < ${#active_paths[@]}; index++)); do
      if [[ "${active_owners[$index]}" == "old" ]]; then
        printf 'active %s\n' "${active_paths[$index]}"
      fi
    done
    for ((index = 0; index < ${#removed_paths[@]}; index++)); do
      if [[ "${removed_owners[$index]}" == "old" ]]; then
        printf 'remove %s\n' "${removed_paths[$index]}"
      fi
    done
  } > "$temporary_file"; then
    rm -f "$temporary_file"
    echo "Failed to stage the ownership inventory checkpoint." >&2
    return 1
  fi
  if ! chmod 644 "$temporary_file"; then
    rm -f "$temporary_file"
    echo "Failed to set package ownership metadata permissions: $temporary_file" >&2
    return 1
  fi
  if ! mv -f "$temporary_file" "$target_file"; then
    rm -f "$temporary_file"
    echo "Failed to commit the ownership inventory checkpoint: $target_file" >&2
    return 1
  fi
  file_count=$((file_count + 1))
}

if [[ "$same_root" -eq 0 ]]; then
  if [[ "$old_inventory_mode" == "directories" || "$old_inventory_mode" == "none" ]]; then
    commit_inventory_checkpoint
  fi

  for metadata_order in 1 2; do
    for ((i = 0; i < ${#plan_rel[@]}; i++)); do
      [[ "${plan_metadata_order[$i]}" -eq "$metadata_order" ]] || continue
      action="${plan_action[$i]}"
      if [[ "$action" != "CREATE" && "$action" != "REPLACE" ]]; then
        continue
      fi
      commit_metadata_file "${plan_source[$i]}" "${plan_target[$i]}"
    done
  done
fi

echo "Upgraded package files at: $target_path"
echo "Merged manifest directories: $manifest_directory_count"
echo "Copied package files: $file_count"
echo "Removed retired package files: $removed_file_count"
echo "Created missing runtime entries: $created_runtime_count"
echo "Existing .gitignore domain rules are preserved; only secret and technical-cache baseline rules are added."
