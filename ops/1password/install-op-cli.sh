#!/bin/bash
# install-op-cli.sh — install the 1Password CLI in a Linux cloud container (Claude Code on the web setup script).
# Needs network access to cache.agilebits.com and keyserver.ubuntu.com. Auth: OP_SERVICE_ACCOUNT_TOKEN from the environment settings.
# The binary is installed only after its GPG signature verifies against 1Password's published signing key.
# Exits non-zero if the token is missing or doesn't authenticate, so a broken setup is visible instead of silent.
set -eu
OP_VERSION="${OP_VERSION:-v2.30.0}"   # bump to the current release from app-updates.agilebits.com/product_history/CLI2
OP_SIGNER_FPR="3FEF9748469ADBE15DA7CA80AC2D62742012EA22"   # 1Password CLI signing key (developer.1password.com/docs/cli/verify) gitleaks:allow (public)

if ! command -v op >/dev/null; then
  command -v gpg >/dev/null || { echo "gpg is required to verify the 1Password CLI; install gnupg first" >&2; exit 1; }
  case "$(uname -m)" in x86_64) ARCH=amd64;; aarch64|arm64) ARCH=arm64;; *) echo "unsupported arch" >&2; exit 1;; esac
  TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
  curl -fsSL -o "$TMP/op.zip" "https://cache.agilebits.com/dist/1P/op2/pkg/${OP_VERSION}/op_linux_${ARCH}_${OP_VERSION}.zip"
  unzip -q -o "$TMP/op.zip" -d "$TMP"
  export GNUPGHOME="$TMP/gnupg"; mkdir -m 700 "$GNUPGHOME"
  gpg --batch --quiet --keyserver hkps://keyserver.ubuntu.com --receive-keys "$OP_SIGNER_FPR" \
    || { echo "could not fetch the 1Password signing key from keyserver.ubuntu.com: allow that host in the environment's network settings (see ops/1password/SETUP.md B.4)" >&2; exit 1; }
  gpg --batch --quiet --verify "$TMP/op.sig" "$TMP/op" 2>"$TMP/verify.log" \
    && grep -q "$OP_SIGNER_FPR" <(gpg --batch --status-fd 1 --verify "$TMP/op.sig" "$TMP/op" 2>/dev/null) \
    || { cat "$TMP/verify.log" >&2; echo "1Password CLI signature did NOT verify; not installing" >&2; exit 1; }
  install -m 0755 "$TMP/op" /usr/local/bin/op
fi
op --version

if [ -z "${OP_SERVICE_ACCOUNT_TOKEN:-}" ]; then
  echo "OP_SERVICE_ACCOUNT_TOKEN is not set. Add it in the environment settings (never in chat or files)." >&2
  exit 1
fi
if ! op whoami >/dev/null 2>&1; then
  echo "OP_SERVICE_ACCOUNT_TOKEN is set but does not authenticate (expired, revoked or wrong). Create/rotate it in 1Password." >&2
  exit 1
fi
echo "1Password service account OK"
