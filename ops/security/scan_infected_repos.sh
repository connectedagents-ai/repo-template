#!/bin/bash
# scan_infected_repos.sh — READ-ONLY: find repos hit by the credential-stealing workflow worm ("build-bot"), on EVERY branch.
#
#   bash ops/security/scan_infected_repos.sh                 # checks Connected-Energy-AI and connectedagents-ai
#   bash ops/security/scan_infected_repos.sh some-owner ...  # other accounts
#
# A branch is listed when it has commits by $BOT_EMAIL, or a workflow matching $IOC_PATTERN (pipes base64 into bash,
# calls the attacker's server, or is named SysDiag). Empty repos are skipped; any other API error is reported as
# UNREACHABLE, never as infected. Changes nothing. The result is also copied to the clipboard (macOS) and saved to
# ~/infected-scan.txt. Needs: gh signed in.
set -u
[ $# -ge 1 ] || set -- Connected-Energy-AI connectedagents-ai
OUT="${OUT:-$HOME/infected-scan.txt}"
BOT_EMAIL="${BOT_EMAIL:-ci-bot@automated.dev}"
IOC_PATTERN="${IOC_PATTERN:-base64 -d \| bash|216\.126\.225\.129|SysDiag}"
: > "$OUT"
found=0
unreachable=0

# api <path> <jq>: prints the filtered result; exit 2 = empty repo (409), 1 = any other error
api() {
  local body
  if body="$(gh api "$1" -q "$2" 2>/dev/null)"; then printf '%s\n' "$body"; return 0; fi
  case "$body" in *"empty"*|*"409"*) return 2 ;; esac
  return 1
}

report() { echo "$1" | tee -a "$OUT"; }

for owner in "$@"; do
  echo "Checking ${owner}..." >&2
  repos="$(gh repo list "$owner" --limit 1000 --json name -q '.[].name')" || { report "could not list ${owner} (gh auth?)"; continue; }
  for r in $repos; do
    branches="$(api "repos/${owner}/${r}/branches?per_page=100" '.[].name')"
    case $? in
      2) continue ;;
      1) report "UNREACHABLE  ${owner}/${r}  (could not list branches)"; unreachable=$((unreachable + 1)); continue ;;
    esac
    for b in $branches; do
      n="$(api "repos/${owner}/${r}/commits?sha=${b}&author=${BOT_EMAIL}&per_page=10" 'length')" || n="?"
      bad=""
      wf="$(api "repos/${owner}/${r}/contents/.github/workflows?ref=${b}" '.[].name')"  # no folder = 404 = no workflows
      for f in $wf; do
        api "repos/${owner}/${r}/contents/.github/workflows/${f}?ref=${b}" '.content' | base64 -d 2>/dev/null \
          | grep -qE "$IOC_PATTERN" && bad="$bad $f"
      done
      if [ "$n" = "?" ]; then
        report "UNREACHABLE  ${owner}/${r}@${b}  (commit check failed)"; unreachable=$((unreachable + 1))
      fi
      if { [ "$n" != "?" ] && [ "$n" != 0 ]; } || [ -n "$bad" ]; then
        report "INFECTED  ${owner}/${r}@${b}  build-bot commits: ${n}  bad workflows:${bad:- none left}"
        found=$((found + 1))
      fi
    done
  done
done
report "scan finished: $found infected branch(es), $unreachable unreachable"
if command -v pbcopy >/dev/null; then pbcopy < "$OUT" && echo "(copied to clipboard: paste it into Claude)"; fi
exit 0
