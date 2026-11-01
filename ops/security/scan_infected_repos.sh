#!/bin/bash
# scan_infected_repos.sh — READ-ONLY: find repos hit by the credential-stealing workflow worm ("build-bot"), on EVERY branch.
#
#   bash ops/security/scan_infected_repos.sh                 # checks Connected-Energy-AI and connectedagents-ai
#   bash ops/security/scan_infected_repos.sh some-owner ...  # other accounts
#
# A branch is listed when it has commits by $BOT_EMAIL, or a workflow matching $IOC_PATTERN (pipes base64 into bash,
# calls the attacker's server, or is named SysDiag). Every page of repos and branches is read. Empty repos are skipped
# and a missing workflows folder means no workflows; any other API error (an owner that can't be listed, a branch,
# commit or workflow check that fails) is reported as UNREACHABLE, never as clean or infected. Changes nothing.
# The result is also copied to the clipboard (macOS) and saved to ~/infected-scan.txt. Needs: gh signed in.
set -u
[ $# -ge 1 ] || set -- Connected-Energy-AI connectedagents-ai
OUT="${OUT:-$HOME/infected-scan.txt}"
BOT_EMAIL="${BOT_EMAIL:-ci-bot@automated.dev}"
IOC_PATTERN="${IOC_PATTERN:-base64 -d \| bash|216\.126\.225\.129|SysDiag}"
: > "$OUT"
found=0
unreachable=0

# api <path> <jq> [gh flags]: prints the filtered result; exit 2 = empty repo (409), 3 = not found (404), 1 = any other error
api() {
  local body
  if body="$(gh api "${@:3}" "$1" -q "$2" 2>/dev/null)"; then printf '%s\n' "$body"; return 0; fi
  case "$body" in *'"409"'*|*"is empty"*) return 2 ;; *'"404"'*) return 3 ;; esac
  return 1
}
REPO_LIMIT=100000

report() { echo "$1" | tee -a "$OUT"; }

for owner in "$@"; do
  echo "Checking ${owner}..." >&2
  if ! repos="$(gh repo list "$owner" --limit "$REPO_LIMIT" --json name -q '.[].name')"; then
    report "UNREACHABLE  ${owner}  (could not list repos: gh auth?)"; unreachable=$((unreachable + 1)); continue
  fi
  for r in $repos; do
    branches="$(api "repos/${owner}/${r}/branches?per_page=100" '.[].name' --paginate)"
    case $? in
      0) ;;
      2) continue ;;
      *) report "UNREACHABLE  ${owner}/${r}  (could not list branches)"; unreachable=$((unreachable + 1)); continue ;;
    esac
    for b in $branches; do
      # branch and file names go in as encoded parameters, so &, # or spaces can't change the request
      n="$(api "repos/${owner}/${r}/commits" 'length' -X GET -f sha="$b" -f author="$BOT_EMAIL" -f per_page=10)" || n="?"
      bad=""
      wf_failed=""
      wf="$(api "repos/${owner}/${r}/contents/.github/workflows" '.[].name' -X GET -f ref="$b")"
      case $? in 0|3) ;; *) wf_failed="workflow list" ;; esac  # 3 = no workflows folder
      while IFS= read -r f; do
        [ -n "$f" ] || continue
        enc="$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$f")"
        if content="$(api "repos/${owner}/${r}/contents/.github/workflows/${enc}" '.content' -X GET -f ref="$b")"; then
          printf '%s' "$content" | base64 -d 2>/dev/null | grep -qE "$IOC_PATTERN" && bad="$bad $f"
        else
          wf_failed="${wf_failed:+$wf_failed, }$f"
        fi
      done <<< "$wf"
      failed=""
      [ "$n" = "?" ] && failed="commits"
      [ -n "$wf_failed" ] && failed="${failed:+$failed, }$wf_failed"
      if [ -n "$failed" ]; then
        report "UNREACHABLE  ${owner}/${r}@${b}  (check failed: ${failed})"; unreachable=$((unreachable + 1))
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
