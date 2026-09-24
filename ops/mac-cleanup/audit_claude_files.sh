#!/bin/bash
# audit_claude_files.sh — READ-ONLY inventory of every Claude-related file on this Mac.
# Changes nothing. Writes a Markdown report to ~/claude-audit-YYYYMMDD-HHMMSS.md
#
#   bash audit_claude_files.sh            # scan $HOME (default depth 6)
#   DEPTH=8 bash audit_claude_files.sh    # scan deeper
#
# Compatible with macOS /bin/bash 3.2.

set -u
DEPTH="${DEPTH:-6}"
STAMP="$(date +%Y%m%d-%H%M%S)"
REPORT="${REPORT:-$HOME/claude-audit-$STAMP.md}"
DESKTOP_DIR="$HOME/Library/Application Support/Claude"
DESKTOP_CFG="$DESKTOP_DIR/claude_desktop_config.json"

hash_file() { if command -v md5 >/dev/null 2>&1; then md5 -q "$1"; else md5sum "$1" | cut -d' ' -f1; fi; }
size_of()   { du -sh "$1" 2>/dev/null | cut -f1; }
out()       { printf '%s\n' "$*" >> "$REPORT"; }

: > "$REPORT"
out "# Claude files audit — $(date)"
out ""
out "Host: $(hostname)  ·  Home: $HOME  ·  Scan depth: $DEPTH"
out ""

# ── 1. Installed Claude Code binaries (beginners often have 2-3 installs) ──
out "## 1. Claude Code installs"
out ""
out '```'
if command -v claude >/dev/null 2>&1; then
  which -a claude 2>/dev/null | while read -r b; do
    printf '%s  →  %s\n' "$b" "$("$b" --version 2>/dev/null | head -1)" >> "$REPORT"
  done
else
  out "claude: not on PATH"
fi
[ -d "$HOME/.claude/local" ] && out "Legacy local install dir present: ~/.claude/local ($(size_of "$HOME/.claude/local"))"
if command -v npm >/dev/null 2>&1; then
  npm ls -g --depth=0 2>/dev/null | grep -i 'anthropic' >> "$REPORT" || out "npm global: no @anthropic-ai packages"
fi
command -v brew >/dev/null 2>&1 && brew list --cask 2>/dev/null | grep -i claude >> "$REPORT"
out '```'
out ""
out "> More than one line above = duplicate installs. Keep ONE (the native installer: \`claude install\`)."
out ""

# ── 2. ~/.claude contents ──
out "## 2. ~/.claude (Claude Code user dir)"
out ""
if [ -d "$HOME/.claude" ]; then
  out "| Path | Size | Notes |"
  out "|---|---|---|"
  for p in "$HOME"/.claude/* "$HOME"/.claude/.[!.]*; do
    [ -e "$p" ] || continue
    name="${p#$HOME/}"
    note=""
    case "$(basename "$p")" in
      projects)        note="session transcripts ($(find "$p" -maxdepth 1 -mindepth 1 -type d | wc -l | tr -d ' ') projects, $(find "$p" -maxdepth 1 -mindepth 1 -type d -mtime +30 | wc -l | tr -d ' ') idle >30d)";;
      todos|shell-snapshots|statsig|debug|ide|file-history|paste-cache) note="cache — safe to archive";;
      CLAUDE.md)       note="global memory — $(wc -l < "$p" | tr -d ' ') lines (aim for < 60)";;
      settings*.json)  note="settings — keep, review";;
      commands|agents|skills|plugins|hooks) note="$(find "$p" -type f | wc -l | tr -d ' ') files — review for dupes";;
      local)           note="legacy local install";;
    esac
    out "| \`~/$name\` | $(size_of "$p") | $note |"
  done
else
  out "_not present_"
fi
[ -f "$HOME/.claude.json" ] && out "" && out "\`~/.claude.json\` (login + per-project state + user MCP servers): $(size_of "$HOME/.claude.json"). **Never move — back up only.**"
out ""

# ── 3. Claude Desktop MCP servers ──
out "## 3. Claude Desktop MCP config"
out ""
if [ -f "$DESKTOP_CFG" ]; then
  out "File: \`$DESKTOP_CFG\`"
  out ""
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$DESKTOP_CFG" >> "$REPORT" <<'PY'
import json, re, sys
cfg = json.load(open(sys.argv[1]))
servers = cfg.get("mcpServers", {})
print(f"{len(servers)} servers defined in JSON (extension-managed servers are NOT listed here):\n")
print("| Server | Command | Inline secrets |")
print("|---|---|---|")
seen = {}
for name, s in servers.items():
    cmd = " ".join([s.get("command", "")] + [str(a) for a in s.get("args", [])])[:90]
    env = s.get("env", {}) or {}
    secrets = [k for k, v in env.items() if re.search(r"KEY|TOKEN|SECRET|PASSWORD", k, re.I) and v and not str(v).startswith("op://")]
    print(f"| `{name}` | `{cmd}` | {', '.join(secrets) or '—'} |")
    seen.setdefault(name.lower().replace("-", "").replace("_", ""), []).append(name)
dupes = [v for v in seen.values() if len(v) > 1]
if dupes:
    print("\n**Duplicate server names:** " + "; ".join(" / ".join(d) for d in dupes))
PY
  else
    grep -oE '"[A-Za-z0-9 _.-]+"[[:space:]]*:[[:space:]]*\{' "$DESKTOP_CFG" >> "$REPORT"
  fi
else
  out "_no claude_desktop_config.json_"
fi
if [ -d "$DESKTOP_DIR/Claude Extensions" ]; then
  out ""
  out "Installed Desktop extensions:"
  out ""
  ls -1 "$DESKTOP_DIR/Claude Extensions" | sed 's/^/- /' >> "$REPORT"
fi
[ -d "$HOME/Library/Logs/Claude" ] && out "" && out "Desktop logs: \`~/Library/Logs/Claude\` ($(size_of "$HOME/Library/Logs/Claude")) — failing servers log to \`mcp-server-<name>.log\` there."
out ""

# ── 4. Stray Claude files scattered around $HOME ──
out "## 4. Claude files scattered across your home folder"
out ""
TMP="$(mktemp)"
find "$HOME" -maxdepth "$DEPTH" \
  \( -path "$HOME/Library" -o -path "$HOME/.Trash" -o -path "$HOME/.claude" -o -name node_modules -o -name .git -o -name .venv -o -path "$HOME/Archive" \) -prune -o \
  \( -name 'CLAUDE.md' -o -name 'CLAUDE.local.md' -o -name '.mcp.json' -o -name 'claude_desktop_config*.json' -o -name 'mcp*.json' \
     -o \( -type d -name '.claude' \) \) -print 2>/dev/null > "$TMP"
out "| File | Size | md5 |"
out "|---|---|---|"
while IFS= read -r f; do
  if [ -f "$f" ]; then h="$(hash_file "$f")"; else h="(dir)"; fi
  out "| \`${f#$HOME/}\` | $(size_of "$f") | $h |"
done < "$TMP"
out ""
out "$(wc -l < "$TMP" | tr -d ' ') items found."
out ""
out "### Identical copies (same md5)"
out ""
out '```'
while IFS= read -r f; do [ -f "$f" ] && printf '%s  %s\n' "$(hash_file "$f")" "${f#$HOME/}"; done < "$TMP" \
  | sort | awk '{c[$1]++; l[$1]=l[$1] "\n    " $2} END {for (k in c) if (c[k]>1) print k l[k]}' >> "$REPORT"
out '```'
rm -f "$TMP"
out ""

# ── 5. Other AI coding tools' config dirs ──
out "## 5. Other AI tool folders"
out ""
out "| Path | Size |"
out "|---|---|"
for d in .cursor .codex .gemini .gemini/antigravity .continue .windsurf .codeium .aider .copilot .config/github-copilot .opencode .amp .qodo .agent-central .mcp; do
  [ -e "$HOME/$d" ] && out "| \`~/$d\` | $(size_of "$HOME/$d") |"
done
out ""

# ── 6. Git repos on this Mac ──
out "## 6. Git repos on this Mac"
out ""
out "Canonical GitHub org: **${CANON_ORG:-connectedagents-ai}**. Flags: ⚠️loc = lives in Desktop/Downloads/Documents/iCloud · ⚠️org = remote is not the canonical org · ✏️ = uncommitted changes · ⬆️ = unpushed commits · 🚫 = no remote (only copy!)"
out ""
out "| Repo path | Remote | Flags |"
out "|---|---|---|"
TMP="$(mktemp)"; REMOTES="$(mktemp)"
find "$HOME" -maxdepth "$DEPTH" \
  \( -path "$HOME/Library" -o -path "$HOME/.Trash" -o -name node_modules -o -name .venv -o -path "$HOME/Archive" \) -prune -o \
  -type d -name .git -print 2>/dev/null | sed 's|/\.git$||' > "$TMP"
while IFS= read -r r; do
  url="$(git -C "$r" remote get-url origin 2>/dev/null)"
  flags=""
  case "$r" in "$HOME/Desktop"*|"$HOME/Downloads"*|"$HOME/Documents"*|*"Mobile Documents"*) flags="$flags ⚠️loc";; esac
  if [ -z "$url" ]; then flags="$flags 🚫"
  else
    case "$url" in *"${CANON_ORG:-connectedagents-ai}/"*) ;; *) flags="$flags ⚠️org";; esac
    printf '%s\t%s\n' "$(printf '%s' "$url" | sed -E 's#^(git@|https://)([^/:]+)[/:]##; s#\.git$##')" "${r#$HOME/}" >> "$REMOTES"
    [ -n "$(git -C "$r" log --branches --not --remotes --oneline 2>/dev/null | head -1)" ] && flags="$flags ⬆️"
  fi
  [ -n "$(git -C "$r" status --porcelain 2>/dev/null | head -1)" ] && flags="$flags ✏️"
  out "| \`${r#$HOME/}\` | ${url:-—} | $flags |"
done < "$TMP"
out ""
out "$(wc -l < "$TMP" | tr -d ' ') repos found."
out ""
out "### Same GitHub repo cloned more than once"
out ""
out '```'
sort "$REMOTES" | awk -F'\t' '{c[$1]++; l[$1]=l[$1] "\n    " $2} END {for (k in c) if (c[k]>1) print k l[k]}' >> "$REPORT"
out '```'
rm -f "$TMP" "$REMOTES"
out ""

# ── 7. Disk hogs that are safe to regenerate ──
out "## 7. Largest regenerable folders (node_modules, .venv, build caches)"
out ""
out '```'
find "$HOME" -maxdepth "$DEPTH" \( -path "$HOME/Library" -o -path "$HOME/.Trash" \) -prune -o \
  -type d \( -name node_modules -o -name .venv -o -name .next -o -name __pycache__ -o -name .turbo \) -prune -print 2>/dev/null \
  | while IFS= read -r d; do du -sk "$d" 2>/dev/null; done | sort -rn | head -25 \
  | awk '{kb=$1; $1=""; printf "%8.1f MB %s\n", kb/1024, $0}' >> "$REPORT"
out '```'
out ""

# ── 8. Work left inside AI tools' own folders (Codex, Cursor, Antigravity, Grok, Devin, Copilot) ──
out "## 8. AI tool workspaces — code that may not be committed anywhere"
out ""
out "Each folder below is a place where an agent created or edited code. 🚫git = not a git repo (only copy!) · ✏️ = uncommitted · ⬆️ = unpushed · ⚠️org = not connectedagents-ai"
out ""
out "| Tool | Folder | Last change | Git |"
out "|---|---|---|---|"
git_state() {
  d="$1"
  if [ ! -d "$d/.git" ]; then printf '🚫git'; return; fi
  u="$(git -C "$d" remote get-url origin 2>/dev/null)"; s=""
  [ -z "$u" ] && s="$s no-remote"
  case "$u" in ""|*"${CANON_ORG:-connectedagents-ai}/"*) ;; *) s="$s ⚠️org";; esac
  [ -n "$(git -C "$d" status --porcelain 2>/dev/null | head -1)" ] && s="$s ✏️"
  [ -n "$(git -C "$d" log --branches --not --remotes --oneline 2>/dev/null | head -1)" ] && s="$s ⬆️"
  printf '%s' "${s:-✅}"
}
mtime() { if stat -f %Sm -t %Y-%m-%d "$1" >/dev/null 2>&1; then stat -f %Sm -t %Y-%m-%d "$1"; else date -r "$1" +%Y-%m-%d 2>/dev/null; fi; }
# tool|parent folder whose children are projects
for spec in \
  "Antigravity|$HOME/.gemini/antigravity/scratch" \
  "Antigravity|$HOME/.gemini/antigravity/playground" \
  "Antigravity|$HOME/.antigravity/projects" \
  "Codex|$HOME/.codex/worktrees" \
  "Codex|$HOME/Documents/Codex" \
  "Cursor|$HOME/.cursor/worktrees" \
  "Cursor|$HOME/Documents/Cursor" \
  "Grok|$HOME/.grok/workspaces" \
  "Grok|$HOME/.grok/projects" \
  "Devin|$HOME/.devin" \
  "Devin|$HOME/Devin" \
  "Copilot|$HOME/Documents/Copilot" \
  "Copilot|$HOME/Library/CloudStorage/OneDrive-*/Copilot"; do
  tool="${spec%%|*}"; parent="${spec#*|}"
  for p in $parent; do
    [ -d "$p" ] || continue
    for d in "$p"/*/; do
      [ -d "$d" ] || continue; d="${d%/}"
      out "| $tool | \`${d#$HOME/}\` | $(mtime "$d") | $(git_state "$d") |"
    done
  done
done
out ""
out "### Tool state (sessions, configs, MCP servers)"
out ""
out '```'
[ -d "$HOME/.codex" ] && {
  out "Codex: $(find "$HOME/.codex/sessions" -type f 2>/dev/null | wc -l | tr -d ' ') session files, $(size_of "$HOME/.codex")"
  [ -f "$HOME/.codex/config.toml" ] && out "  config.toml MCP servers: $(grep -oE '^\[mcp_servers\.[^]]+' "$HOME/.codex/config.toml" | sed 's/\[mcp_servers\.//' | tr '\n' ' ')"
  [ -f "$HOME/.codex/AGENTS.md" ] && out "  global AGENTS.md: $(wc -l < "$HOME/.codex/AGENTS.md" | tr -d ' ') lines"
}
[ -f "$HOME/.cursor/mcp.json" ] && command -v python3 >/dev/null 2>&1 && \
  out "Cursor mcp.json servers: $(python3 -c 'import json,sys;print(" ".join(json.load(open(sys.argv[1])).get("mcpServers",{})))' "$HOME/.cursor/mcp.json" 2>/dev/null)"
[ -d "$HOME/.gemini" ] && out "Gemini/Antigravity: $(size_of "$HOME/.gemini"); GEMINI.md: $( [ -f "$HOME/.gemini/GEMINI.md" ] && echo "$(wc -l < "$HOME/.gemini/GEMINI.md" | tr -d ' ') lines" || echo none)"
[ -d "$HOME/.gemini/antigravity/brain" ] && out "Antigravity brain (agent artifacts): $(find "$HOME/.gemini/antigravity/brain" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ') conversations, $(size_of "$HOME/.gemini/antigravity/brain")"
[ -d "$HOME/.gemini/antigravity/knowledge" ] && out "Antigravity knowledge items: $(find "$HOME/.gemini/antigravity/knowledge" -type f | wc -l | tr -d ' ') files"
[ -f "$HOME/.gemini/antigravity/mcp_config.json" ] && command -v python3 >/dev/null 2>&1 && \
  out "Antigravity mcp_config.json servers: $(python3 -c 'import json,sys;print(" ".join(json.load(open(sys.argv[1])).get("mcpServers",{})))' "$HOME/.gemini/antigravity/mcp_config.json" 2>/dev/null)"
[ -f "$HOME/.gemini/settings.json" ] && command -v python3 >/dev/null 2>&1 && \
  out "Gemini CLI settings.json MCP servers: $(python3 -c 'import json,sys;print(" ".join(json.load(open(sys.argv[1])).get("mcpServers",{})))' "$HOME/.gemini/settings.json" 2>/dev/null)"
[ -d "$HOME/Library/CloudStorage" ] && out "Cloud drives mounted: $(ls "$HOME/Library/CloudStorage" 2>/dev/null | tr '\n' ' ')"
[ -d "$HOME/.grok" ] && out "Grok CLI: $(size_of "$HOME/.grok")"
for d in "$HOME/Library/Application Support/Perplexity" "$HOME/Library/Application Support/Comet" "$HOME/Library/Application Support/ChatGPT" "$HOME/Library/Application Support/com.openai.chat"; do
  [ -d "$d" ] && out "$(basename "$d") desktop app data: $(size_of "$d")"
done
n="$(find "$HOME/Downloads" "$HOME/Desktop" "$HOME/Documents" -maxdepth 3 -type f \( -iname '*perplexity*' -o -iname '*chatgpt*' -o -iname '*grok*' -o -iname '*copilot*' -o -iname 'conversations.json' \) 2>/dev/null | wc -l | tr -d ' ')"
out "Loose AI exports in Downloads/Desktop/Documents (name mentions perplexity/chatgpt/grok/copilot): $n files → ingest with ops/ai-library/ingest_library.py"
for app in Cursor Antigravity Windsurf "Code"; do
  ws="$HOME/Library/Application Support/$app/User/workspaceStorage"
  [ -d "$ws" ] || continue
  out ""
  out "$app — folders opened (from workspaceStorage), missing ones = stale:"
  cat "$ws"/*/workspace.json 2>/dev/null | grep -oE '"folder"[[:space:]]*:[[:space:]]*"file://[^"]+' | sed -E 's#.*file://##' \
    | sed 's/%20/ /g' | sort -u | while IFS= read -r f; do
      if [ -d "$f" ]; then printf '  %s  [%s]\n' "${f#$HOME/}" "$(git_state "$f")"; else printf '  %s  [MISSING]\n' "${f#$HOME/}"; fi
    done >> "$REPORT"
done
out '```'
out ""
out "Cloud-only tools (Devin sessions, Microsoft 365 Copilot, Codex cloud, Cursor background agents, Grok) keep work on their servers or in GitHub branches — see ops/github-consolidation/MIGRATION-PLAN.md."
out ""
out "---"
out "Next: \`bash collect_ai_workspaces.sh\` and \`bash archive_claude_files.sh\` (both dry-run by default) → review → re-run with \`--apply\`."

echo "Report written: $REPORT"
