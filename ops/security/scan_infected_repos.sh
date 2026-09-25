#!/bin/bash
# scan_infected_repos.sh — READ-ONLY: find repos hit by the 2026-05-18 credential-stealing workflow ("build-bot").
#
#   bash ops/security/scan_infected_repos.sh                 # checks Connected-Energy-AI and connectedagents-ai
#   bash ops/security/scan_infected_repos.sh some-owner ...  # other accounts
#
# A repo is listed when it has commits by ci-bot@automated.dev, or a workflow that pipes base64 into bash, calls the
# attacker's server (216.126.225.129) or is named SysDiag. Changes nothing. The result is also copied to the clipboard
# (macOS) and saved to ~/infected-scan.txt. Needs: gh signed in.
set -u
[ $# -ge 1 ] || set -- Connected-Energy-AI connectedagents-ai
OUT="${OUT:-$HOME/infected-scan.txt}"
: > "$OUT"
found=0
for owner in "$@"; do
  echo "Checking $owner…" >&2
  repos="$(gh repo list "$owner" --limit 500 --json name -q '.[].name')" || { echo "could not list $owner (gh auth?)" | tee -a "$OUT"; continue; }
  for r in $repos; do
    n="$(gh api "repos/$owner/$r/commits?author=ci-bot@automated.dev&per_page=10" -q 'length' 2>/dev/null)"
    bad=""
    for f in $(gh api "repos/$owner/$r/contents/.github/workflows" -q '.[].name' 2>/dev/null); do
      gh api "repos/$owner/$r/contents/.github/workflows/$f" -q .content 2>/dev/null | base64 -d 2>/dev/null \
        | grep -qE 'base64 -d \| bash|216\.126\.225\.129|SysDiag' && bad="$bad $f"
    done
    if [ "${n:-0}" != 0 ] || [ -n "$bad" ]; then
      echo "INFECTED  $owner/$r  build-bot commits: ${n:-0}  bad workflows:${bad:- none left}" | tee -a "$OUT"
      found=$((found + 1))
    fi
  done
done
echo "scan finished: $found infected repo(s)" | tee -a "$OUT"
if command -v pbcopy >/dev/null; then pbcopy < "$OUT" && echo "(copied to clipboard: paste it into Claude)"; fi
exit 0
