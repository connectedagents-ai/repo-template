#!/bin/bash
# inventory_cloud.sh — READ-ONLY inventory of the cloud stack, top-down:
# Entra ID → Azure → Google Cloud → GitHub → Vercel → Cloudflare → 1Password.
# Uses whichever CLIs are installed and logged in; skips the rest. Changes nothing.
# Writes ~/cloud-inventory-YYYYMMDD-HHMMSS.md  (feed it into docs/CLOUD-ARCHITECTURE.md §3)
#
#   bash inventory_cloud.sh
#   INCLUDE_1PASSWORD=0 bash inventory_cloud.sh   # skip 1Password (client discovery passes this unless clause 4b is consented)
# Exits 1 if any command that ran failed (the report is still written, with "(failed: …)" markers).
#
# Logins (once): az login --allow-no-subscriptions · gcloud auth login · gh auth login · vercel login · wrangler login · op signin
# macOS bash 3.2 OK.

set -u
umask 077  # reports list accounts, vaults and history: readable by this user only
OUT="${OUT:-$HOME/cloud-inventory-$(date +%Y%m%d-%H%M%S).md}"
out() { printf '%s\n' "$*" >> "$OUT"; }
FAILED=0
run() { out '```'; "$@" >> "$OUT" 2>&1 || { out "(failed: $*)"; FAILED=1; }; out '```'; out ""; }
have() { command -v "$1" >/dev/null 2>&1 || { out "_$1 not installed — skipped_"; out ""; return 1; }; }

: > "$OUT"
out "# Cloud inventory — $(date)"
out ""

out "## L0 · Microsoft Entra ID"
if have az; then
  run az account show --query '{user:user.name, tenant:tenantId, tenantDomain:tenantDefaultDomain}' -o table
  run az account tenant list --query '[].{tenant:tenantId, name:displayName, domain:defaultDomain}' -o table
  run az rest --method get --url 'https://graph.microsoft.com/v1.0/organization?$select=displayName,verifiedDomains,createdDateTime' --query 'value[].{name:displayName, created:createdDateTime, domains:join(`, `, verifiedDomains[].name)}' -o table
  run az rest --method get --url 'https://graph.microsoft.com/v1.0/subscribedSkus?$select=skuPartNumber,consumedUnits,prepaidUnits' --query 'value[].{sku:skuPartNumber, used:consumedUnits, total:prepaidUnits.enabled}' -o table
  run az ad user list --query 'length(@)' -o tsv
  out "Enterprise apps (SSO-connected services):"
  run az ad sp list --all --filter "tags/any(t:t eq 'WindowsAzureActiveDirectoryIntegratedApp')" --query '[].{app:displayName, created:createdDateTime}' -o table
  out "App registrations (check for stale client secrets):"
  run az ad app list --all --query '[].{app:displayName, secrets:length(passwordCredentials), secretExpiries:join(`", "`, passwordCredentials[?endDateTime].endDateTime)}' -o table
fi

out "## L1 · Azure"
if have az; then
  run az account list --all --query '[].{subscription:name, id:id, state:state, tenant:tenantId}' -o table
  for s in $(az account list --all --query '[].id' -o tsv 2>/dev/null); do
    out "### subscription $s"
    run az resource list --subscription "$s" --query '[].{name:name, type:type, rg:resourceGroup, location:location}' -o table
  done
fi

out "## L1 · Google Cloud"
if have gcloud; then
  run gcloud auth list
  run gcloud organizations list
  run gcloud projects list --format='table(projectId,name,lifecycleState,createTime)'
  run gcloud billing accounts list
  for p in $(gcloud projects list --format='value(projectId)' 2>/dev/null); do
    out "### project $p"
    run gcloud services list --enabled --project "$p" --format='value(config.name)'
    run gcloud run services list --project "$p" --format='table(metadata.name,region,status.url)'
    run gcloud iam service-accounts list --project "$p" --format='table(email,disabled)'
  done
fi

out "## L3 · GitHub"
if have gh; then
  run gh auth status
  run gh api user/orgs --jq '.[].login'
  for o in $(gh api user/orgs --jq '.[].login' 2>/dev/null); do
    out "### org $o"
    run gh repo list "$o" --limit 2000 --json name,isArchived,isFork,pushedAt --jq 'group_by(.isArchived) | map({archived: .[0].isArchived, count: length})'
    run gh api "orgs/$o/installations" --jq '.installations[] | [.app_slug, .repository_selection] | @tsv'
  done
fi

out "## L4 · Vercel"
if have vercel; then run vercel teams ls; run vercel projects ls; fi

out "## L4 · Cloudflare"
if have wrangler; then run wrangler whoami; run wrangler pages project list; fi

out "## L0 · 1Password (names only, never values)"
if [ "${INCLUDE_1PASSWORD:-1}" != 1 ]; then
  out "_skipped: 1Password is a clause 4b source and consent was not given_"
elif have op; then
  run op account list
  run op vault list
  out "Vault sharing (who can open each vault: look for bots and broad shares):"
  for v in $(op vault list --format json 2>/dev/null | python3 -c 'import json,sys;[print(x["id"]) for x in json.load(sys.stdin)]' 2>/dev/null); do
    out "### vault $(op vault get "$v" --format json 2>/dev/null | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("name"), "·", d.get("items", "?"), "items")' 2>/dev/null)"
    run op vault user list "$v"
  done
fi

echo "Inventory written: $OUT"
[ "$FAILED" = 0 ] || { echo "Some commands failed; see the (failed: …) lines in the report." >&2; exit 1; }
