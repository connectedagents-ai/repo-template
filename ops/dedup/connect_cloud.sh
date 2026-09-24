#!/bin/bash
# connect_cloud.sh — one-time: connect Google Drive and/or pCloud accounts so the dedup can list them.
#
#   bash ops/dedup/connect_cloud.sh
#
# Uses rclone (free, open source). Each account opens a browser window to sign in. Google Drive is connected
# READ-ONLY, which is all the dedup scan needs. Nothing is downloaded. Accounts show up as rclone "remotes"
# named like gdrive-powerconnection: or pcloud:. Connect one Google remote per Google login.
set -u
say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
if ! command -v rclone >/dev/null 2>&1; then
  command -v brew >/dev/null 2>&1 || { echo "Install Homebrew first: https://brew.sh (then run this again)"; exit 1; }
  printf 'rclone is not installed. Install it now with Homebrew? (y/n): '; read -r yn
  case "$yn" in y|Y|yes) brew install rclone || exit 1;; *) echo "Skipped. Nothing changed."; exit 0;; esac
fi
say "Already connected:"
rclone listremotes --long | sed 's/^/  /' | grep . || echo "  (none yet)"
while true; do
  printf '\n  Connect which? 1) Google Drive  2) pCloud  q) done: '; read -r c
  case "$c" in
    1) printf '  Short label for this Google login (e.g. powerconnection, personal): '; read -r l
       l="$(printf '%s' "$l" | tr 'A-Z' 'a-z' | tr -cd 'a-z0-9-')"; [ -n "$l" ] || { echo "  Please type a label."; continue; }
       say "A browser window opens: sign in to the Google account for '$l' and click Allow (read-only access)."
       rclone config create "gdrive-$l" drive scope=drive.readonly && echo "  ✅ connected as gdrive-$l:" ;;
    2) printf '  pCloud region? 1) US  2) EU (Europe): '; read -r reg
       host=api.pcloud.com; [ "$reg" = 2 ] && host=eapi.pcloud.com
       say "A browser window opens: sign in to pCloud and allow rclone."
       rclone config create pcloud pcloud hostname="$host" && echo "  ✅ connected as pcloud:" ;;
    q|Q|"") break ;;
    *) echo "  Type 1, 2 or q." ;;
  esac
done
say "Connected accounts:"; rclone listremotes --long | sed 's/^/  /'
echo "  Next: bash ops/dedup/start_here.sh   (it will offer to include these accounts)"
