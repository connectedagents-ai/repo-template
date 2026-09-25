#!/bin/bash
# configure_github.sh — apply the standard settings to a GitHub org and all its repos. DRY RUN by default.
#
#   bash ops/github-setup/configure_github.sh powerconnection                  # preview: prints every change, makes none
#   bash ops/github-setup/configure_github.sh --apply powerconnection          # apply
#   bash ops/github-setup/configure_github.sh --apply --create-repos powerconnection   # also create the blueprint repos
#
# What it sets (docs/GITHUB-SETUP.md explains each one):
#   org        members read-only by default, only owners create repos, no forking private repos
#   team       "maintainers" (used by CODEOWNERS), with you as maintainer
#   Actions    all repos; only GitHub-made, verified-creator and listed actions; workflow token read-only by default
#   security   one "standard" code security configuration on every repo and as the default for new ones:
#              dependency graph, Dependabot alerts + security updates, secret scanning + push protection,
#              private vulnerability reporting
#   ruleset    "protect-main" on every repo's default branch (rulesets/protect-main.json): PR required,
#              CI checks "secrets" and "check" must pass, open review threads resolved, no force-push or deletion
#   repos      squash-merge only (PR title as the commit title), auto-merge on, delete branches after merge,
#              wiki/projects off, Dependabot alerts + security updates on
#   --create-repos  the repos from docs/GITHUB-BLUEPRINT.md §3 that don't exist yet (private, main branch;
#              ".github" is public because GitHub only reads org-wide defaults from a public one; "config" is the template)
# It never deletes, archives, transfers or renames anything, and it is safe to re-run (existing items are updated).
# Some settings need a paid plan on PRIVATE repos (rulesets: Team; secret scanning: Secret Protection). Those calls
# fail with GitHub's message, the run continues, and the summary lists them.
#
# Needs: gh CLI signed in as an org owner (gh auth status), with the admin:org scope:
#   gh auth refresh -h github.com -s admin:org
# Writes github-setup-<date>.log in the current folder. Exits 1 if any change failed. macOS bash 3.2 OK.

set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
APPLY=0 CREATE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --create-repos) CREATE=1 ;;
    -*) echo "unknown option $1" >&2; exit 2 ;;
    *) break ;;
  esac
  shift
done
[ $# -eq 1 ] || { sed -n '2,8p' "$0"; exit 2; }
ORG="$1"
command -v gh >/dev/null || { echo "install the GitHub CLI first: brew install gh" >&2; exit 1; }

LOG="github-setup-$(date +%Y%m%d-%H%M%S).log"
FAILS="$(mktemp)"; trap 'rm -f "$FAILS"' EXIT
# progress goes to the screen (stderr) and the log; stdout carries only API responses, so $(api …) captures JSON
log() { printf '%s\n' "$*" >> "$LOG"; printf '%s\n' "$*" >&2; }

# api METHOD PATH [BODY]: in a dry run print the change; with --apply make it. Prints the response on stdout.
api() {
  local method="$1" path="$2" body="${3:-}" out
  if [ "$APPLY" != 1 ]; then
    log "WOULD $method $path${body:+  $(printf '%s' "$body" | tr -d '\n' | tr -s ' ')}"
    return 0
  fi
  if [ -n "$body" ]; then out="$(printf '%s' "$body" | gh api -X "$method" "$path" --input - 2>&1)"
  else out="$(gh api -X "$method" "$path" 2>&1)"; fi
  if [ $? -eq 0 ]; then log "ok    $method $path"; printf '%s' "$out"
  else log "FAIL  $method $path: $(printf '%s' "$out" | tr '\n' ' ' | cut -c1-300)"; echo "$method $path" >> "$FAILS"; return 1; fi
}

# ---- read-only checks (always run) ----
ME="$(gh api user --jq .login)" || { echo "gh is not signed in: run  gh auth login" >&2; exit 1; }
ROLE="$(gh api "orgs/$ORG/memberships/$ME" --jq .role 2>/dev/null)"
[ "$ROLE" = admin ] || { echo "$ME is not an owner of $ORG (role: ${ROLE:-none}). Create the org or ask an owner." >&2; exit 1; }
PLAN="$(gh api "orgs/$ORG" --jq .plan.name 2>/dev/null)"
log "# GitHub setup for $ORG as $ME (plan: ${PLAN:-unknown}) — $([ "$APPLY" = 1 ] && echo APPLY || echo 'DRY RUN: nothing changes')"

log ""; log "## Organization"
api PATCH "orgs/$ORG" '{
  "default_repository_permission": "read",
  "members_can_create_repositories": false,
  "members_can_create_public_repositories": false,
  "members_can_create_private_repositories": false,
  "members_can_fork_private_repositories": false,
  "members_can_create_public_pages": false
}' >/dev/null

log ""; log "## Team: maintainers"
if gh api "orgs/$ORG/teams/maintainers" >/dev/null 2>&1; then log "exists orgs/$ORG/teams/maintainers"
else api POST "orgs/$ORG/teams" '{"name": "maintainers", "privacy": "closed", "description": "Code owners (CODEOWNERS)"}' >/dev/null; fi
api PUT "orgs/$ORG/teams/maintainers/memberships/$ME" '{"role": "maintainer"}' >/dev/null

log ""; log "## Actions"
api PUT "orgs/$ORG/actions/permissions" '{"enabled_repositories": "all", "allowed_actions": "selected"}' >/dev/null
api PUT "orgs/$ORG/actions/permissions/selected-actions" '{
  "github_owned_allowed": true,
  "verified_allowed": true,
  "patterns_allowed": ["anthropics/claude-code-action@*"]
}' >/dev/null
api PUT "orgs/$ORG/actions/permissions/workflow" '{"default_workflow_permissions": "read", "can_approve_pull_request_reviews": false}' >/dev/null

log ""; log "## Code security configuration: standard"
CONFIG_BODY='{
  "name": "standard",
  "description": "Dependency graph, Dependabot, secret scanning + push protection, private vulnerability reporting",
  "dependency_graph": "enabled",
  "dependabot_alerts": "enabled",
  "dependabot_security_updates": "enabled",
  "secret_scanning": "enabled",
  "secret_scanning_push_protection": "enabled",
  "private_vulnerability_reporting": "enabled",
  "enforcement": "enforced"
}'
CID="$(gh api "orgs/$ORG/code-security/configurations" --jq '.[] | select(.name == "standard") | .id' 2>/dev/null)"
if [ -n "$CID" ]; then api PATCH "orgs/$ORG/code-security/configurations/$CID" "$CONFIG_BODY" >/dev/null
elif [ "$APPLY" = 1 ]; then CID="$(api POST "orgs/$ORG/code-security/configurations" "$CONFIG_BODY" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' 2>/dev/null)"
else api POST "orgs/$ORG/code-security/configurations" "$CONFIG_BODY"; CID="<new id>"; fi
if [ -n "$CID" ]; then
  api POST "orgs/$ORG/code-security/configurations/$CID/attach" '{"scope": "all"}' >/dev/null
  api PUT "orgs/$ORG/code-security/configurations/$CID/defaults" '{"default_for_new_repos": "all"}' >/dev/null
fi

log ""; log "## Ruleset: protect-main"
RULESET="$(cat "$HERE/rulesets/protect-main.json")"
RID="$(gh api "orgs/$ORG/rulesets" --jq '.[] | select(.name == "protect-main") | .id' 2>/dev/null)"
if [ -n "$RID" ]; then api PUT "orgs/$ORG/rulesets/$RID" "$RULESET" >/dev/null
else api POST "orgs/$ORG/rulesets" "$RULESET" >/dev/null; fi

if [ "$CREATE" = 1 ]; then
  log ""; log "## Blueprint repos"
  EXISTING="$(gh repo list "$ORG" --limit 2000 --json name -q '.[].name' 2>/dev/null)"
  while IFS='|' read -r name vis desc; do
    if printf '%s\n' "$EXISTING" | grep -qx "$name"; then log "exists $ORG/$name"; continue; fi
    api POST "orgs/$ORG/repos" "{\"name\": \"$name\", \"private\": $([ "$vis" = public ] && echo false || echo true), \"description\": \"$desc\", \"auto_init\": true, \"has_wiki\": false, \"has_projects\": false}" >/dev/null
  done <<'REPOS'
.github|public|Org profile, default PR and issue templates, reusable workflows
config|private|Rules for every agent (AGENTS.md), Claude settings, dotfiles, MCP templates, ops scripts. Template for new repos
platform|private|Shared MCP servers, SDK packages, agents and skills
powerconnection|private|Power Connection energy business: web, geo, marketing, CRM
onewish|private|OneWish OS and its apps
litigationforce|private|LitigationForce / LexVault product code (no case data)
voice-agents|private|Voice agent platform, console, telephony and realtime clients
lab|private|Experiments and spikes; pruned quarterly; nothing ships from here
REPOS
  api PATCH "repos/$ORG/config" '{"is_template": true}' >/dev/null
fi

log ""; log "## Repository settings (every non-archived repo)"
REPO_BODY='{
  "allow_squash_merge": true,
  "allow_merge_commit": false,
  "allow_rebase_merge": false,
  "squash_merge_commit_title": "PR_TITLE",
  "squash_merge_commit_message": "PR_BODY",
  "allow_auto_merge": true,
  "allow_update_branch": true,
  "delete_branch_on_merge": true,
  "has_wiki": false,
  "has_projects": false
}'
REPOS="$(gh repo list "$ORG" --limit 2000 --no-archived --json name -q '.[].name')" || { log "FAIL  could not list $ORG repos"; echo "list repos" >> "$FAILS"; }
[ "$CREATE" = 1 ] && [ "$APPLY" != 1 ] && log "(the new blueprint repos get these settings on the --apply run)"
for r in ${REPOS:-}; do
  api PATCH "repos/$ORG/$r" "$REPO_BODY" >/dev/null
  api PUT "repos/$ORG/$r/vulnerability-alerts" >/dev/null
  api PUT "repos/$ORG/$r/automated-security-fixes" >/dev/null
done

log ""; log "## Copilot (read-only: seats and policies are set in the web UI, see docs/GITHUB-SETUP.md §3)"
seats="$(gh api "orgs/$ORG/copilot/billing" --jq '"plan: \(.plan_type // "?") · seats: \(.seat_breakdown.total // 0)"' 2>/dev/null)"
log "${seats:-Copilot is not enabled for $ORG (no Copilot Business/Enterprise plan on the org)}"

log ""
if [ -s "$FAILS" ]; then
  log "## $(wc -l < "$FAILS" | tr -d ' ') change(s) FAILED (see the FAIL lines above; 'Upgrade' or 'Advanced Security' messages mean a paid plan is needed for private repos):"
  sed 's/^/  - /' "$FAILS" | tee -a "$LOG" >&2
  exit 1
fi
log "Done. Log: $LOG$([ "$APPLY" = 1 ] || echo '   (dry run: re-run with --apply to make these changes)')"
