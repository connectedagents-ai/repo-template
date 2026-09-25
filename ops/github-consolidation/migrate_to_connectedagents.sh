#!/bin/bash
# migrate_to_connectedagents.sh — move every repo from other GitHub owners into connectedagents-ai.
#
#   bash migrate_to_connectedagents.sh Connected-Energy-AI              # DRY RUN: writes a plan CSV
#   bash migrate_to_connectedagents.sh Connected-Energy-AI some-user    # several source owners
#   bash migrate_to_connectedagents.sh --apply Connected-Energy-AI      # perform the transfers
#
# Rules:
#   * name free in connectedagents-ai   → TRANSFER (GitHub keeps a redirect from the old URL)
#   * name already taken                → COLLISION: never transferred automatically; listed for a
#                                          merge decision (see MIGRATION-PLAN.md). Names planned earlier in
#                                          the same run count as taken, so two owners' "api" can't both move.
#   * EXCLUDE (below)                   → skipped (org meta repos, etc.)
# Transfers are reversible (transfer back) but secrets, webhooks, Actions variables, deploy keys
# and App installations do NOT follow the repo — re-create them afterwards.
#
# Exits non-zero if any owner could not be listed or any transfer failed or was not confirmed.
# Needs: gh CLI logged in as an admin of both owners (`gh auth status`). macOS bash 3.2 OK.

set -u
TARGET="${TARGET:-connectedagents-ai}"
EXCLUDE="${EXCLUDE:-.github .github-private}"
APPLY=0
[ "${1:-}" = "--apply" ] && { APPLY=1; shift; }
[ $# -ge 1 ] || { sed -n '2,16p' "$0"; exit 2; }
command -v gh >/dev/null || { echo "install gh: brew install gh" >&2; exit 1; }

STAMP="$(date +%Y%m%d-%H%M%S)"
PLAN="migration-plan-$STAMP.csv"

# One call for the whole target inventory, so collisions are checked against reality.
# Abort if it can't be fetched: an empty list would make every repo look collision-free.
TARGET_NAMES="$(gh repo list "$TARGET" --limit 2000 --json name -q '.[].name')" || { echo "could not list $TARGET repos (gh auth/network); aborting" >&2; exit 1; }
[ -n "$TARGET_NAMES" ] || { echo "$TARGET returned no repos; refusing to continue without a collision check" >&2; exit 1; }
echo "source,name,target_name,action,archived,fork,visibility" > "$PLAN"

# The loop below runs in a subshell (pipeline), so shared state lives in files.
STATE="$(mktemp -d)"; trap 'rm -rf "$STATE"' EXIT
TAKEN="$STATE/taken"; FAILED="$STATE/failed"
printf '%s\n' "$TARGET_NAMES" | tr 'A-Z' 'a-z' > "$TAKEN"
: > "$FAILED"

# Unconfirmed transfer: find out who holds the repo now and put its archived state back there.
settle_unconfirmed() {
  local src="$1" name="$2" archived="$3" owner
  owner="$(gh api "repos/$src/$name" --jq .owner.login 2>/dev/null)"  # GitHub redirects a moved repo
  echo "    ⏳ transfer of $src/$name NOT confirmed after 2 min; the repo is currently owned by: ${owner:-unknown}" >&2
  [ "$archived" = true ] || return 0
  # It was unarchived for the move, so until it is re-archived it is writable wherever it now lives.
  if [ -n "$owner" ] && gh repo archive "$owner/$name" --yes >/dev/null 2>&1; then
    echo "    re-archived $owner/$name" >&2
  else
    echo "    ⚠ ARCHIVE NOT RESTORED: find $name (under $src or $TARGET) and run  gh repo archive <owner>/$name --yes  before continuing" >&2
    echo "$src/$name (archive NOT restored; repo is writable)" >> "$FAILED"
  fi
}

for SRC in "$@"; do
  SRC_REPOS="$(gh repo list "$SRC" --limit 2000 --json name,isArchived,isFork,visibility \
    -q '.[] | [.name, .isArchived, .isFork, .visibility] | @tsv')" || { echo "could not list $SRC repos; skipping $SRC" >&2; echo "$SRC (listing failed)" >> "$FAILED"; continue; }
  printf '%s\n' "$SRC_REPOS" | grep -v '^$' |
  while IFS="$(printf '\t')" read -r name archived fork vis; do
    lname="$(printf '%s' "$name" | tr 'A-Z' 'a-z')"
    action="transfer"
    case " $EXCLUDE " in *" $name "*) action="skip-excluded";; esac
    if [ "$action" = transfer ] && grep -qxF "$lname" "$TAKEN"; then
      action="collision-needs-merge"
    fi
    [ "$action" = transfer ] && echo "$lname" >> "$TAKEN"
    echo "$SRC,$name,$name,$action,$archived,$fork,$vis" >> "$PLAN"
    printf '%-24s %-50s %s\n' "$action" "$SRC/$name" "$( [ "$archived" = true ] && echo '(archived)')"

    if [ "$APPLY" = 1 ] && [ "$action" = transfer ]; then
      # Archived repos are read-only and cannot be transferred: unarchive, move, re-archive.
      [ "$archived" = true ] && gh repo unarchive "$SRC/$name" --yes >/dev/null
      if gh api -X POST "repos/$SRC/$name/transfer" -f new_owner="$TARGET" >/dev/null; then
        # transfers are asynchronous: wait (up to ~2 min) until the repo answers under the new owner
        tries=0
        arrived=0
        until [ "$tries" -ge "${TRANSFER_WAIT_TRIES:-24}" ]; do
          if gh api "repos/$TARGET/$name" --jq .full_name 2>/dev/null | grep -qix "$TARGET/$name"; then arrived=1; break; fi
          sleep "${TRANSFER_WAIT_SECS:-5}"; tries=$((tries + 1))
        done
        if [ "$arrived" = 0 ]; then
          settle_unconfirmed "$SRC" "$name" "$archived"
          echo "$SRC/$name (not confirmed)" >> "$FAILED"
          continue
        fi
        echo "    ✓ moved → $TARGET/$name"
        if [ "$archived" = true ]; then
          gh repo archive "$TARGET/$name" --yes >/dev/null 2>&1 \
            || echo "    ⚠ transferred but NOT re-archived: run  gh repo archive $TARGET/$name --yes" >&2
        fi
      else
        echo "    ✗ transfer failed for $SRC/$name (check org 'allow repo transfer' setting / your admin rights)" >&2
        echo "$SRC/$name (failed)" >> "$FAILED"
        if [ "$archived" = true ]; then
          gh repo archive "$SRC/$name" --yes >/dev/null 2>&1 \
            || echo "    ⚠ could not re-archive $SRC/$name: run  gh repo archive $SRC/$name --yes" >&2
        fi
      fi
    fi
  done
done

echo
echo "Plan written: $PLAN"
[ "$APPLY" = 1 ] || echo "Dry run only. Review the CSV and resolve collisions, then re-run with --apply."
if [ -s "$FAILED" ]; then
  echo "NOT everything worked. Fix these, then re-run:" >&2
  sed 's/^/  /' "$FAILED" >&2
  exit 1
fi
