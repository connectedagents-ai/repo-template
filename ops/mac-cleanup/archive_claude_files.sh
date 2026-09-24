#!/bin/bash
# archive_claude_files.sh — ARCHIVE-ONLY cleanup of beginner-era Claude files.
# Never deletes. Moves clutter into ~/Archive/claude-legacy-<stamp>/, snapshots all
# live config there too, and writes a manifest plus a restore.sh that undoes every move.
#
#   bash archive_claude_files.sh                 # DRY RUN (default): prints the plan
#   bash archive_claude_files.sh --apply         # do it
#   IDLE_DAYS=60 bash archive_claude_files.sh    # only archive transcripts idle > 60 days (default 30)
#   bash archive_claude_files.sh --apply --install-desktop-config templates/claude_desktop_config.json
#   bash archive_claude_files.sh --apply --prune-mcp        # remove the legacy MCP servers listed in PRUNE_MCP
#   PRUNE_MCP="git shell" bash archive_claude_files.sh --prune-mcp   # custom list
#
# Quit Claude Desktop and every running `claude` session before --apply.
# Compatible with macOS /bin/bash 3.2.

set -u
APPLY=0
NEW_DESKTOP_CFG=""
PRUNE=0
# Legacy servers from the beginner-era Claude Desktop config: duplicates, overlapping shell tools, broken ones,
# and ones replaced by built-ins or connectors. Kept: playwright, firecrawl and 1password (fix it: absolute op path + sign in).
PRUNE_MCP="${PRUNE_MCP:-filesystem memory sequential-thinking github git desktop-automation applescript shell sqlite email grok}"
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --install-desktop-config) shift; NEW_DESKTOP_CFG="${1:-}" ;;
    --prune-mcp) PRUNE=1 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

IDLE_DAYS="${IDLE_DAYS:-30}"
DEPTH="${DEPTH:-6}"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="${ARCHIVE_ROOT:-$HOME/Archive}/claude-legacy-$STAMP"
DESKTOP_DIR="$HOME/Library/Application Support/Claude"
DESKTOP_CFG="$DESKTOP_DIR/claude_desktop_config.json"
MANIFEST="$DEST/MANIFEST.tsv"
RESTORE="$DEST/restore.sh"

say() { printf '%s\n' "$*"; }

if [ "$APPLY" = 1 ]; then
  if [ -z "${SKIP_RUNNING_CHECK:-}" ] && { pgrep -x Claude >/dev/null 2>&1 || pgrep -f '(^|/)claude( |$)' >/dev/null 2>&1; }; then
    say "Claude Desktop or a claude CLI session is running. Quit them first, then re-run." >&2
    exit 1
  fi
  mkdir -p "$DEST/snapshot" "$DEST/moved"
  printf 'action\tfrom\tto\n' > "$MANIFEST"
  printf '#!/bin/bash\n# Undo archive_claude_files.sh run %s\nset -e\n' "$STAMP" > "$RESTORE"
  chmod +x "$RESTORE"
  say "APPLY mode → $DEST"
else
  say "DRY RUN — nothing will change. Re-run with --apply to execute. Archive would be: $DEST"
fi
say ""

# Copy (never move) live config so there is a full reference snapshot.
snapshot() {
  src="$1"; [ -e "$src" ] || return 0
  rel="${src#$HOME/}"
  say "  snapshot  ~/$rel"
  [ "$APPLY" = 1 ] || return 0
  mkdir -p "$DEST/snapshot/$(dirname "$rel")"
  cp -Rp "$src" "$DEST/snapshot/$rel"
  printf 'snapshot\t%s\t%s\n' "$src" "$DEST/snapshot/$rel" >> "$MANIFEST"
}

# Move into the archive, recording how to put it back.
archive() {
  src="$1"; why="$2"; [ -e "$src" ] || return 0
  rel="${src#$HOME/}"
  say "  archive   ~/$rel   ($why)"

  [ "$APPLY" = 1 ] || return 0
  dst="$DEST/moved/$rel"
  mkdir -p "$(dirname "$dst")"
  mv "$src" "$dst"
  printf 'move\t%s\t%s\n' "$src" "$dst" >> "$MANIFEST"
  printf 'mkdir -p "%s" && mv "%s" "%s"\n' "$(dirname "$src")" "$dst" "$src" >> "$RESTORE"
}

say "1) Snapshot live config (copied, left in place)"
snapshot "$HOME/.claude.json"
for f in settings.json settings.local.json CLAUDE.md keybindings.json commands agents skills hooks plugins; do
  snapshot "$HOME/.claude/$f"
done
snapshot "$DESKTOP_CFG"
say ""

say "2) Claude Code caches (recreated automatically)"
for d in todos shell-snapshots statsig debug ide paste-cache file-history; do
  archive "$HOME/.claude/$d" "cache"
done
say ""

say "3) Session transcripts idle > $IDLE_DAYS days (~/.claude/projects)"
if [ -d "$HOME/.claude/projects" ]; then
  find "$HOME/.claude/projects" -mindepth 1 -maxdepth 1 -type d -mtime +"$IDLE_DAYS" 2>/dev/null | while IFS= read -r d; do
    # a project dir is idle only if nothing inside changed recently either
    if [ -z "$(find "$d" -type f -mtime -"$IDLE_DAYS" -print -quit 2>/dev/null)" ]; then
      archive "$d" "idle transcript"
    fi
  done
fi
say ""

say "4) Legacy local install (only if another claude binary exists)"
if [ -d "$HOME/.claude/local" ]; then
  other="$(which -a claude 2>/dev/null | grep -v "$HOME/.claude/local" | head -1)"
  if [ -n "$other" ]; then archive "$HOME/.claude/local" "superseded by $other"
  else say "  keep      ~/.claude/local (it is your only install)"; fi
fi
say ""

say "5) Old Claude Desktop logs (> $IDLE_DAYS days)"
if [ -d "$HOME/Library/Logs/Claude" ]; then
  find "$HOME/Library/Logs/Claude" -type f -name '*.log*' -mtime +"$IDLE_DAYS" 2>/dev/null | while IFS= read -r f; do
    archive "$f" "old log"
  done
fi
say ""

say "6) Stray config copies outside their real homes"
find "$HOME" -maxdepth "$DEPTH" \
  \( -path "$HOME/Library" -o -path "$HOME/.Trash" -o -path "$HOME/.claude" -o -path "$HOME/Archive" -o -name node_modules -o -name .git -o -name .venv \) -prune -o \
  -type f \( -name 'claude_desktop_config*.json' -o -name 'claude_desktop_config*.bak' -o -name 'CLAUDE.md.bak' -o -name 'CLAUDE.md.old' -o -name 'CLAUDE copy*.md' -o -name 'CLAUDE (*).md' \) \
  -print 2>/dev/null | while IFS= read -r f; do
    archive "$f" "stray copy"
  done
say "  (CLAUDE.md files inside real git repos are LEFT ALONE — review them from the audit report.)"
say ""

if [ -n "$NEW_DESKTOP_CFG" ]; then
  say "7) Replace Claude Desktop MCP config with $NEW_DESKTOP_CFG"
  if [ ! -f "$NEW_DESKTOP_CFG" ]; then say "  missing: $NEW_DESKTOP_CFG" >&2; exit 1; fi
  if command -v python3 >/dev/null 2>&1 && ! python3 -m json.tool "$NEW_DESKTOP_CFG" >/dev/null; then
    say "  invalid JSON: $NEW_DESKTOP_CFG" >&2; exit 1
  fi
  say "  install   $NEW_DESKTOP_CFG → $DESKTOP_CFG (old copy is in the snapshot)"
  if [ "$APPLY" = 1 ]; then
    [ -f "$DESKTOP_CFG" ] && printf 'cp "%s" "%s"\n' "$DEST/snapshot/${DESKTOP_CFG#$HOME/}" "$DESKTOP_CFG" >> "$RESTORE"
    mkdir -p "$DESKTOP_DIR"
    cp "$NEW_DESKTOP_CFG" "$DESKTOP_CFG"
    printf 'install\t%s\t%s\n' "$NEW_DESKTOP_CFG" "$DESKTOP_CFG" >> "$MANIFEST"
  fi
  say ""
fi

if [ "$PRUNE" = 1 ]; then
  say "8) Prune legacy MCP servers from Claude Desktop config"
  if [ ! -f "$DESKTOP_CFG" ]; then say "  no config at $DESKTOP_CFG"
  elif ! command -v python3 >/dev/null 2>&1; then say "  python3 needed (xcode-select --install)" >&2
  else
    APPLY="$APPLY" PRUNE_MCP="$PRUNE_MCP" python3 - "$DESKTOP_CFG" <<'PYEOF'
import json, os, sys
path = sys.argv[1]
cfg = json.load(open(path))
servers = cfg.get("mcpServers", {})
drop = set(os.environ["PRUNE_MCP"].split())
for name in list(servers):
    if name in drop:
        print(f"  remove    {name}")
        if os.environ["APPLY"] == "1":
            del servers[name]
    else:
        env = servers[name].get("env") or {}
        inline = [k for k, v in env.items() if v and any(w in k.upper() for w in ("KEY", "TOKEN", "SECRET")) and not str(v).startswith("op://")]
        print(f"  keep      {name}" + (f"   ⚠ inline secret {', '.join(inline)}: move to 1Password" if inline else ""))
if os.environ["APPLY"] == "1":
    json.dump(cfg, open(path, "w"), indent=2)
PYEOF
    [ "$APPLY" = 1 ] && printf 'cp "%s" "%s"\n' "$DEST/snapshot/${DESKTOP_CFG#$HOME/}" "$DESKTOP_CFG" >> "$RESTORE"
  fi
  say "  Extension-managed servers can't be removed here. In Claude Desktop → Settings → Extensions, remove:"
  say "    Control Chrome (use the built-in Claude in Chrome instead) · Read and Send iMessages (unless you use it)"
  say ""
fi

if [ "$APPLY" = 1 ]; then
  say "Done. Manifest: $MANIFEST"
  say "Undo everything: bash \"$RESTORE\""
else
  say "Dry run complete. Re-run with --apply to execute."
fi
