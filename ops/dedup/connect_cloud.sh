#!/bin/bash
# connect_cloud.sh — one-time: connect Google Drive, OneDrive / SharePoint and/or pCloud accounts so the dedup can list them.
#
#   bash ops/dedup/connect_cloud.sh
#
# Uses rclone (free, open source). Each account opens a browser window to sign in. Google Drive is connected
# READ-ONLY, which is all the dedup scan needs. Nothing is downloaded. Accounts show up as rclone "remotes"
# named like gdrive-powerconnection:, onedrive-onewishlabs:, sp-legalmatters: or pcloud:.
# Connect one remote per Google login, per Microsoft account/tenant, and per SharePoint site you want checked.
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
  printf '\n  Connect which? 1) Google Drive  2) pCloud  3) OneDrive  4) a SharePoint site  q) done: '; read -r c
  case "$c" in
    1) printf '  Short label for this Google login (e.g. powerconnection, personal): '; read -r l
       l="$(printf '%s' "$l" | tr 'A-Z' 'a-z' | tr -cd 'a-z0-9-')"; [ -n "$l" ] || { echo "  Please type a label."; continue; }
       say "A browser window opens: sign in to the Google account for '$l' and click Allow (read-only access)."
       rclone config create "gdrive-$l" drive scope=drive.readonly && echo "  ✅ connected as gdrive-$l:" ;;
    2) printf '  pCloud region? 1) US  2) EU (Europe): '; read -r reg
       host=api.pcloud.com; [ "$reg" = 2 ] && host=eapi.pcloud.com
       say "A browser window opens: sign in to pCloud and allow rclone."
       rclone config create pcloud pcloud hostname="$host" && echo "  ✅ connected as pcloud:" ;;
    3|4) kind=onedrive; [ "$c" = 4 ] && kind=sp
       printf '  Short label (e.g. onewishlabs, netzerolending, personal%s): ' "$( [ "$c" = 4 ] && echo ', or the site name like legalmatters')"; read -r l
       l="$(printf '%s' "$l" | tr 'A-Z' 'a-z' | tr -cd 'a-z0-9-')"; [ -n "$l" ] || { echo "  Please type a label."; continue; }
       say "Answer rclone's questions like this:"
       echo "   • region: 1 (Microsoft Cloud Global) · client_id / client_secret: press Return · edit advanced config: n"
       echo "   • 'Use web browser to automatically authenticate': y → sign in with the account for '$l'"
       if [ "$c" = 3 ]; then
         echo "   • type of connection: 'OneDrive Personal or Business', then pick the drive it lists (usually the first)"
       else
         echo "   • type of connection: 'Sharepoint site name or URL' → paste the site URL (e.g. https://<tenant>.sharepoint.com/sites/LEGALMATTERS),"
         echo "     then pick the document library it lists (usually 'Documents' / 'Shared Documents')"
       fi
       echo "   • confirm with y. Microsoft grants read and write; the dedup scan only reads, and nothing is downloaded."
       rclone config create "$kind-$l" onedrive && echo "  ✅ connected as $kind-$l:" ;;
    q|Q|"") break ;;
    *) echo "  Type 1, 2, 3, 4 or q." ;;
  esac
done
say "Connected accounts:"; rclone listremotes --long | sed 's/^/  /'
echo "  Next: bash ops/dedup/start_here.sh   (it will offer to include these accounts)"
