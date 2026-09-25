#!/bin/bash
# check_domains.sh — READ-ONLY: who hosts DNS, who receives mail, what's verified, where the web points, registrar + expiry.
#   bash check_domains.sh connectedsolar.com getconnectedenergy.com netzerolending.io baileyco.us powerconnection.com
# Run before and after changes. macOS: dig/whois/curl are built in.
set -u
[ $# -ge 1 ] || set -- connectedsolar.com getconnectedenergy.com netzerolending.io baileyco.us connectedenergyservices.com connectedenergy.ai powerconnection.com
for d in "$@"; do
  echo "=== $d"
  echo "  registrar : $(whois "$d" 2>/dev/null | grep -iE '^ *registrar:' | head -1 | sed 's/.*: *//')"
  echo "  expires   : $(whois "$d" 2>/dev/null | grep -iE 'expir' | head -1 | sed 's/.*: *//')"
  echo "  NS        : $(dig +short NS "$d" | tr '\n' ' ')"
  # dig exits non-zero on timeout/SERVFAIL; +short hides NXDOMAIN, so check the status header too
  mx_raw="$(dig +short +time=5 +tries=2 MX "$d")"; mx_rc=$?
  status="$(dig +noall +comments +time=5 +tries=2 MX "$d" | grep -oE 'status: [A-Z]+' | head -1 | cut -d' ' -f2)"
  mx="$(printf '%s\n' "$mx_raw" | grep -v '^;;' | sort -n | tr '\n' ' ' | sed 's/ *$//')"
  if [ "$mx_rc" -ne 0 ] || [ -z "$status" ]; then
    echo "  MX        : ⚠ LOOKUP FAILED (dig exit $mx_rc) — unknown, NOT 'no mail'. Re-run before changing anything."
  elif [ "$status" != "NOERROR" ]; then
    echo "  MX        : ⚠ DNS status $status — domain may be expired/parked; treat mail as unknown"
  else
    echo "  MX        : ${mx:-(none — lookup succeeded, no MX records)}"
  fi
  case "$mx" in
    *google.com*|*googlemail*) echo "              → mail is on Google Workspace";;
    *outlook.com*|*protection.outlook*) echo "              → mail is on Microsoft 365 (a tenant owns this domain: migrate/remove it there first)";;
    *secureserver.net*) echo "              → mail is on GoDaddy (Workspace email or forwarding)";;
  esac
  echo "  SPF       : $(dig +short TXT "$d" | grep -i 'v=spf1' | tr -d '"')"
  echo "  verif.    : $(dig +short TXT "$d" | grep -ioE '(google-site-verification|MS=ms[0-9]+)' | sort -u | tr '\n' ' ')"
  echo "  DMARC     : $(dig +short TXT "_dmarc.$d" | tr -d '"')"
  for u in "http://$d" "https://$d" "https://www.$d"; do
    res="$(curl -sS -o /dev/null -m 10 -w '%{http_code} %{redirect_url}' "$u" 2>&1)"; rc=$?
    if [ "$rc" -ne 0 ]; then echo "  web       : $u  ⚠ REQUEST FAILED (curl exit $rc): $res"
    else
      code="${res%% *}"; target="${res#* }"
      scheme="$(printf '%s' "$target" | sed -nE 's#^([a-zA-Z]+)://.*#\1#p' | tr 'A-Z' 'a-z')"
      host="$(printf '%s' "$target" | sed -E 's#^[a-zA-Z]+://([^/:?#]+).*#\1#' | tr 'A-Z' 'a-z')"
      case "$code:$scheme:$host" in
        301:https:powerconnection.com|301:https:www.powerconnection.com) flag="✅ permanent redirect";;
        308:https:powerconnection.com|308:https:www.powerconnection.com) flag="⚠ 308 is permanent, but this runbook uses 301 (older clients handle it best)";;
        30[1278]:http:powerconnection.com|30[1278]:http:www.powerconnection.com) flag="⚠ redirects over plain http: point it at https://";;
        30[27]:https:powerconnection.com|30[27]:https:www.powerconnection.com) flag="⚠ $code is temporary: use 301";;
        30?:*) flag="↪ redirects elsewhere ($host), not to powerconnection.com";;
        *) flag="";;
      esac
      echo "  web       : $u  $code → ${target:-(none)} $flag"
    fi
  done
done
