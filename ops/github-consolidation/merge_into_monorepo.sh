#!/bin/bash
# merge_into_monorepo.sh — fold a repo into a subfolder of a target repo, keeping its full history.
# Works on a fresh branch in a temporary clone and pushes that branch so you can review it as a PR. Nothing is archived or deleted.
#
#   bash merge_into_monorepo.sh <target-repo> <source owner/repo> <path/in/target>          # DRY RUN
#   bash merge_into_monorepo.sh --apply onewish-os connectedagents-ai/onewishos packages/onewishos
#
# After the PR merges, archive the source:  gh repo archive <source owner/repo> --yes
# macOS bash 3.2 OK. Needs git + gh (logged in).

set -eu
APPLY=0; [ "${1:-}" = "--apply" ] && { APPLY=1; shift; }
[ $# -eq 3 ] || { sed -n '2,10p' "$0"; exit 2; }
ORG="${ORG:-connectedagents-ai}"
TARGET="$1"; SOURCE="$2"; PREFIX="${3%/}"
BRANCH="chore/fold-in-$(basename "$SOURCE" | tr 'A-Z' 'a-z')"
BASE="${GIT_BASE_URL:-https://github.com}"

echo "target : $ORG/$TARGET  →  $PREFIX/"
echo "source : $SOURCE"
echo "branch : $BRANCH"
[ "$APPLY" = 1 ] || { echo "Dry run. Re-run with --apply."; exit 0; }

WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
git clone -q "$BASE/$ORG/$TARGET.git" "$WORK/t"
cd "$WORK/t"
[ -e "$PREFIX" ] && { echo "$PREFIX already exists in $TARGET, so pick another path" >&2; exit 1; }
git checkout -q -b "$BRANCH"
git remote add src "$BASE/$SOURCE.git"
git fetch -q src
SRC_HEAD="$(git remote show src | sed -n 's/.*HEAD branch: //p')"
git merge -q -s ours --no-commit --allow-unrelated-histories "src/$SRC_HEAD"
git read-tree --prefix="$PREFIX/" -u "src/$SRC_HEAD"
git commit -q -m "chore: fold $SOURCE into $PREFIX/ (history preserved)"
git remote remove src
git push -q -u origin "$BRANCH"
echo "Pushed $BRANCH. Open the PR:  gh pr create -R $ORG/$TARGET -H $BRANCH -f"
