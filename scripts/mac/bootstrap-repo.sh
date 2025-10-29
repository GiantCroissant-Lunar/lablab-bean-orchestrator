#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $(basename "$0") --type <unity|dotnet|python> --path <repo-path>"
}

TYPE=""; DEST=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --type) TYPE="$2"; shift 2;;
    --path) DEST="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 1;;
  esac
done

if [ -z "$TYPE" ] || [ -z "$DEST" ]; then usage; exit 1; fi

ROOT=$(cd "$(dirname "$0")/../.." && pwd)

copy_common() {
  cp "$ROOT/templates/common/.editorconfig" "$DEST/.editorconfig" || true
  cp "$ROOT/templates/common/.gitattributes" "$DEST/.gitattributes" || true
}

case "$TYPE" in
  unity)
    mkdir -p "$DEST/scripts/precommit/unity" "$DEST/scripts/precommit/common"
    cp "$ROOT/templates/unity/.pre-commit-config.yaml" "$DEST/.pre-commit-config.yaml"
    cp "$ROOT/templates/unity/.gitignore" "$DEST/.gitignore"
    cp "$ROOT/templates/unity/Taskfile.yml" "$DEST/Taskfile.yml"
    cp "$ROOT/templates/unity/scripts/precommit/unity/check_meta_pairs.py" "$DEST/scripts/precommit/unity/check_meta_pairs.py"
    cp "$ROOT/templates/unity/scripts/precommit/unity/check_editor_settings.py" "$DEST/scripts/precommit/unity/check_editor_settings.py"
    cp "$ROOT/templates/unity/scripts/precommit/common/check_lfs.py" "$DEST/scripts/precommit/common/check_lfs.py"
    ;;
  dotnet)
    cp "$ROOT/templates/dotnet/.pre-commit-config.yaml" "$DEST/.pre-commit-config.yaml"
    cp "$ROOT/templates/dotnet/Taskfile.yml" "$DEST/Taskfile.yml"
    ;;
  python)
    cp "$ROOT/templates/python/.pre-commit-config.yaml" "$DEST/.pre-commit-config.yaml"
    cp "$ROOT/templates/python/Taskfile.yml" "$DEST/Taskfile.yml"
    ;;
  *) echo "Unknown type: $TYPE"; exit 1;;
esac

copy_common

if command -v pre-commit >/dev/null 2>&1; then
  (cd "$DEST" && pre-commit install)
else
  echo "pre-commit not installed; skip installing hook."
fi

echo "Bootstrapped $TYPE repo at $DEST"
