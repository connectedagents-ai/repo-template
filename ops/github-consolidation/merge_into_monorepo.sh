#!/bin/bash
# merge_into_monorepo.sh — fold a repo into a subfolder of a target repo, keeping its full history.
# Works on a fresh branch in a temporary clone and pushes that branch so you can review it as a PR. Nothing is archived or deleted.
#
#   bash merge_into_monorepo.sh <target-repo> <source owner/repo> <path/in/target>          # DRY RUN
#   bash merge_into_monorepo.sh --apply onewish-os connectedagents-ai/onewishos packages/onewishos
#
# Only the source's default branch is folded in. If the source has other branches with unmerged work, the
# script lists them and stops: merge or export them first, or re-run with FOLD_ACK_BRANCHES=1 to accept losing them.
# After the PR merges, archive the source:  gh repo archive <source owner/repo> --yes
# macOS bash 3.2 OK. Needs git + gh (logged in).

set -eu
APPLY=0; [ "${1:-}" = "--apply" ] && { APPLY=1; shift; }
[ $# -eq 3 ] || { sed -n '2,12p' "$0"; exit 2; }
ORG="${ORG:-connectedagents-ai}"
TARGET="$1"; SOURCE="$2"; PREFIX="${3%/}"
BRANCH="chore/fold-in-$(basename "$SOURCE" | tr 'A-Z' 'a-z')"
BASE="${GIT_BASE_URL:-https://github.com}"

echo "target : $ORG/$TARGET  →  $PREFIX/"
echo "source : $SOURCE"
echo "branch : $BRANCH"
if [ "$APPLY" != 1 ]; then
  echo "source branches (only the default branch is folded in):"
  git ls-remote --heads "$BASE/$SOURCE.git" | sed 's|.*refs/heads/|  |' || echo "  (could not list branches)"
  echo "Dry run. Re-run with --apply."
  exit 0
fi

WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
git clone -q "$BASE/$ORG/$TARGET.git" "$WORK/t"
cd "$WORK/t"
[ -e "$PREFIX" ] && { echo "$PREFIX already exists in $TARGET, so pick another path" >&2; exit 1; }
git checkout -q -b "$BRANCH"
git remote add src "$BASE/$SOURCE.git"
git fetch -q src
SRC_HEAD="$(git remote show src | sed -n 's/.*HEAD branch: //p')"
UNMERGED="$(git for-each-ref --format='%(refname:short)' --no-merged "src/$SRC_HEAD" refs/remotes/src | grep -vx "src/HEAD\|src" || true)"
if [ -n "$UNMERGED" ] && [ "${FOLD_ACK_BRANCHES:-0}" != 1 ]; then
  echo "These $SOURCE branches have work that is not on $SRC_HEAD and would NOT be folded in:" >&2
  printf '  %s\n' $UNMERGED >&2
  echo "Merge or export them first, or re-run with FOLD_ACK_BRANCHES=1 to go ahead without them." >&2
  exit 1
fi
git merge -q --no-ff -s ours --no-commit --allow-unrelated-histories "src/$SRC_HEAD"
git read-tree --prefix="$PREFIX/" -u "src/$SRC_HEAD"
git commit -q -m "chore: fold $SOURCE into $PREFIX/ (history preserved)"
git remote remove src
git push -q -u origin "$BRANCH"
echo "Pushed $BRANCH. Open the PR:  gh pr create -R $ORG/$TARGET -H $BRANCH -f"
