#!/bin/bash
# connect_browsers.sh — open Microsoft Edge and Google Chrome in windows Claude Code can drive, and connect them to it.
#
#   bash ops/cowork/connect_browsers.sh          # Edge (port 9222) and Chrome (port 9223)
#   bash ops/cowork/connect_browsers.sh edge     # just one of them
#
# Each browser gets its own profile folder in ~/.claude-browsers/ (browsers refuse agent control of your everyday
# profile). Sign in to GitHub and Google once in each window; the logins are kept for next time. Claude Code on this Mac
# then drives the windows through the Playwright MCP servers named "edge" and "chrome". You still type every password
# and 2FA code. The control ports only listen on this Mac. Quit the windows when you're done. Safe to re-run.
set -u
PROFILES="${PROFILES:-$HOME/.claude-browsers}"
EDGE_BIN="${EDGE_BIN:-/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge}"
CHROME_BIN="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
[ $# -ge 1 ] || set -- edge chrome
command -v claude >/dev/null || { echo "install Claude Code first: curl -fsSL https://claude.ai/install.sh | bash" >&2; exit 1; }
command -v npx >/dev/null || { echo "install Node.js first: brew install node" >&2; exit 1; }

up() { curl -fs "http://127.0.0.1:$1/json/version" >/dev/null 2>&1; }

connect() {  # name, browser binary, port
  local name="$1" bin="$2" port="$3"
  [ -x "$bin" ] || { echo "SKIP $name: not installed at $bin"; return 1; }
  if ! up "$port"; then
    mkdir -p "$PROFILES/$name"
    "$bin" --user-data-dir="$PROFILES/$name" --remote-debugging-port="$port" --no-first-run \
      https://github.com/login https://accounts.google.com >/dev/null 2>&1 &
    for _ in $(seq 1 "${WAIT_SECS:-30}"); do up "$port" && break; sleep 1; done
  fi
  up "$port" || { echo "FAIL $name: its control port $port did not open"; return 1; }
  claude mcp get "$name" >/dev/null 2>&1 \
    || claude mcp add --scope user "$name" -- npx -y @playwright/mcp@latest --cdp-endpoint "http://127.0.0.1:$port" >/dev/null \
    || { echo "FAIL $name: could not register it with Claude Code"; return 1; }
  echo "OK   $name is open and connected to Claude Code (MCP server \"$name\")"
}

failed=0
for b in "$@"; do
  case "$b" in
    edge) connect edge "$EDGE_BIN" 9222 || failed=1 ;;
    chrome) connect chrome "$CHROME_BIN" 9223 || failed=1 ;;
    *) echo "unknown browser: $b (use edge or chrome)"; failed=1 ;;
  esac
done
cat <<'EOF'

Next:
  1. In each new window, sign in to GitHub and Google (only the first time).
  2. Start Claude Code here, reachable from your phone too:  cd ~/Code/repo-template && claude remote-control
  3. Tell it, for example: "Use the edge browser. Follow ops/cowork/TASKS.md, starting with the ground rules and Task 1."
EOF
exit "$failed"
