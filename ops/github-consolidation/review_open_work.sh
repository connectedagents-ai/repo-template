#!/bin/bash
# review_open_work.sh — READ-ONLY: for every repo of a GitHub owner, list the work that is not yet merged:
# open pull requests, and branches that have commits the default branch doesn't have. Changes nothing.
#
#   bash ops/github-consolidation/review_open_work.sh Connected-Energy-AI
#
# Writes open-work-<owner>-<date>.csv in the current folder and prints the repos that need a look.
# Exits 1 if any repo could not be checked (its row shows "?"). Needs: gh signed in (gh auth status). macOS bash 3.2 OK.

set -u
OWNER="${1:?usage: review_open_work.sh <github-owner>}"
command -v gh >/dev/null || { echo "install the GitHub CLI first: brew install gh" >&2; exit 1; }
OUT="${OUT:-open-work-$OWNER-$(date +%Y%m%d-%H%M%S).csv}"
LIST="$(mktemp)"; trap 'rm -f "$LIST"' EXIT
FAILED=0

gh repo list "$OWNER" --limit 1000 --json name,isArchived,isFork,pushedAt,defaultBranchRef \
  -q '.[] | [.name, .isArchived, .isFork, .pushedAt, (.defaultBranchRef.name // "")] | @tsv' > "$LIST" \
  || { echo "could not list $OWNER repos (gh auth or network)" >&2; exit 1; }

echo "repo,archived,fork,last_push,default_branch,open_prs,branches_ahead,branches" > "$OUT"
while IFS="$(printf '\t')" read -r name archived fork pushed def; do
  prs="$(gh pr list -R "$OWNER/$name" --state open --json number -q length 2>/dev/null)" || { prs="?"; FAILED=1; }
  n=0 ahead=""
  if [ -n "$def" ]; then
    branches="$(gh api "repos/$OWNER/$name/branches" --paginate -q '.[].name' 2>/dev/null)" || { branches=""; n="?"; FAILED=1; }
    for b in $branches; do
      [ "$b" = "$def" ] && continue
      a="$(gh api "repos/$OWNER/$name/compare/$def...$b" -q .ahead_by 2>/dev/null)" || { a="?"; FAILED=1; }
      [ "$a" = 0 ] && continue
      [ "$n" != "?" ] && n=$((n + 1))
      ahead="$ahead $b(+$a)"
    done
  fi
  echo "$name,$archived,$fork,$pushed,$def,$prs,$n,\"${ahead# }\"" >> "$OUT"
done < "$LIST"

echo "Report: $OUT"
echo "Repos with open PRs or unmerged branches (review these before anything moves):"
awk -F, 'NR > 1 && ($6 != "0" || $7 != "0") { printf "  %-45s open PRs: %-3s unmerged branches: %s %s\n", $1, $6, $7, $8 }' "$OUT"
[ "$FAILED" = 0 ] || { echo "Some repos could not be checked (marked ?). Re-run, or check them by hand." >&2; exit 1; }
