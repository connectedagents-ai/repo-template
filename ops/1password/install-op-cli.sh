#!/bin/bash
# install-op-cli.sh — install the 1Password CLI in a Linux cloud container (Claude Code on the web setup script).
# Needs network access to cache.agilebits.com. Auth comes from OP_SERVICE_ACCOUNT_TOKEN in the environment settings.
set -eu
command -v op >/dev/null && { op --version; exit 0; }
OP_VERSION="${OP_VERSION:-v2.30.0}"   # bump to the current release from app-updates.agilebits.com/product_history/CLI2
case "$(uname -m)" in x86_64) ARCH=amd64;; aarch64|arm64) ARCH=arm64;; *) echo "unsupported arch" >&2; exit 1;; esac
TMP="$(mktemp -d)"
curl -fsSL -o "$TMP/op.zip" "https://cache.agilebits.com/dist/1P/op2/pkg/${OP_VERSION}/op_linux_${ARCH}_${OP_VERSION}.zip"
unzip -q -o "$TMP/op.zip" -d "$TMP"
install -m 0755 "$TMP/op" /usr/local/bin/op
rm -rf "$TMP"
op --version
[ -n "${OP_SERVICE_ACCOUNT_TOKEN:-}" ] && op whoami >/dev/null && echo "1Password service account OK" || echo "OP_SERVICE_ACCOUNT_TOKEN not set (add it in the environment settings)"
