#!/bin/bash
# check_domains.sh — READ-ONLY: who hosts DNS, who receives mail, what's verified, where the web points, registrar + expiry.
#   bash check_domains.sh connectedsolar.com getconnectedenergy.com netzerolending.io baileyco.us powerconnection.com
# Run before and after changes. macOS: dig/whois/curl are built in.
set -u
[ $# -ge 1 ] || set -- connectedsolar.com getconnectedenergy.com netzerolending.io baileyco.us connectedenergyservices.com powerconnection.com
for d in "$@"; do
  echo "=== $d"
  echo "  registrar : $(whois "$d" 2>/dev/null | grep -iE '^ *registrar:' | head -1 | sed 's/.*: *//')"
  echo "  expires   : $(whois "$d" 2>/dev/null | grep -iE 'expir' | head -1 | sed 's/.*: *//')"
  echo "  NS        : $(dig +short NS "$d" | tr '\n' ' ')"
  mx="$(dig +short MX "$d" | sort -n | tr '\n' ' ')"
  echo "  MX        : ${mx:-(none — domain receives no mail)}"
  case "$mx" in
    *google.com*|*googlemail*) echo "              → mail is on Google Workspace";;
    *outlook.com*|*protection.outlook*) echo "              → mail is on Microsoft 365 (a tenant owns this domain: migrate/remove it there first)";;
    *secureserver.net*) echo "              → mail is on GoDaddy (Workspace email or forwarding)";;
  esac
  echo "  SPF       : $(dig +short TXT "$d" | grep -i 'v=spf1' | tr -d '"')"
  echo "  verif.    : $(dig +short TXT "$d" | grep -ioE '(google-site-verification|MS=ms[0-9]+)' | sort -u | tr '\n' ' ')"
  echo "  DMARC     : $(dig +short TXT "_dmarc.$d" | tr -d '"')"
  echo "  web       : $(curl -sI -m 10 "http://$d" | grep -iE '^(HTTP|location)' | tr -d '\r' | tr '\n' ' ')"
done
