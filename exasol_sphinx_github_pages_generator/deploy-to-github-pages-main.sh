#!/bin/bash

PUSH_ENABLED="$1"

set -euo pipefail

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
SOURCE_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "$SOURCE_BRANCH" == "main" ]; then
  TARGET_BRANCH="$("$SCRIPT_DIR/get_target_branch_name.sh" "main")"
  python3 "$SCRIPT_DIR/deploy-github-pages.py" --target_branch "$TARGET_BRANCH" --push_origin origin --push_enabled "$PUSH_ENABLED" --source_branch "$SOURCE_BRANCH"
else
  echo "Abort. Source branch is not 'main', you are at branch '$SOURCE_BRANCH'"
fi
