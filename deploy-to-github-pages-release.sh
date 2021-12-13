#!/bin/bash

set -euo pipefail

PUSH_ENABLED="$1"

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

TAG="$(git describe --tags --exact-match)"
if [ -n "$TAG" ]; then
  TARGET_BRANCH="$("$SCRIPT_DIR/get_target_branch_name.sh" "main")"
  python3 "$SCRIPT_DIR/deploy-github-pages.py" --target_branch "$TARGET_BRANCH" --push_origin origin --push_enabled "$PUSH_ENABLED" --source_branch "$TAG"
else
  echo "ERROR: Could not acquire your current checked out tag. Please check the state of your working copy"
fi