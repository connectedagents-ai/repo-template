# Point legacy domains at powerconnection.com (GoDaddy + Google Workspace)

Goal: `connectedsolar.com`, `getconnectedenergy.com`, `netzerolending.io`, `baileyco.us` (and optionally `connectedenergyservices.com`)
→ **web** redirects to https://powerconnection.com and **email** to any address @those domains lands in the matching @powerconnection.com inbox.

## 0. Pre-flight (do not skip: these domains may still carry live mail or legal evidence)
Run `bash ops/domains/check_domains.sh` on the Mac and record the output (the "before" snapshot) in the platform register.

| If the check shows… | Then |
|---|---|
| **MX → Microsoft 365** (likely for `netzerolending.io`, which has its own tenant) | That tenant owns the domain's mail. **Export mailboxes first** (Purview), then remove the domain from that tenant (M365 admin → Settings → Domains → Remove), and only then continue. Otherwise mail silently breaks |
| **MX → Google (another Workspace)** | Remove the domain from that Workspace first. A domain can belong to only one Google Workspace |
| **MX → GoDaddy / other with existing mailboxes** (e.g. old staff addresses on `getconnectedenergy.com`) | Export those mailboxes first. They may be **litigation evidence**: check with counsel about preservation before changing MX |
| **NS not GoDaddy** (e.g. Cloudflare) | Make the DNS changes where the nameservers point, not in GoDaddy |
| Expiry soon / auto-renew off | Turn on auto-renew in GoDaddy now |

## 1. Email: add each domain as a *user alias domain* in Google Workspace
Result: `anyone@connectedsolar.com` is delivered to `anyone@powerconnection.com` for every existing user, at no extra license cost.

1. admin.google.com (as a powerconnection.com super admin) → **Account → Domains → Manage domains → Add a domain**.
2. Enter the domain → choose **User alias domain** → Add and start verification.
3. Google shows a **TXT verification record** → GoDaddy → My Products → the domain → **DNS** → Add record: Type `TXT`, Name `@`, Value = Google's string → Save → back in Google click **Verify**. It usually works within minutes, but can take up to 48 hours.
4. **Activate Gmail** for the alias domain: in GoDaddy DNS, delete the existing MX records and add Google's MX record: Type `MX`, Name `@`, Value `smtp.google.com`, Priority `1`.
   (If Google's setup screen shows a different set, e.g. the 5 older `aspmx.l.google.com` records, use exactly what it shows.)
5. **SPF:** one TXT record on `@`: `v=spf1 include:_spf.google.com ~all` (replace any existing SPF; a domain must have only one).
6. **DKIM:** admin.google.com → Apps → Google Workspace → Gmail → **Authenticate email** → select the domain → Generate new record → add the `google._domainkey` TXT in GoDaddy → **Start authentication**.
7. **DMARC:** TXT, Name `_dmarc`, Value `v=DMARC1; p=none; rua=mailto:rbailey@powerconnection.com`. Move to `p=quarantine` after 2–4 weeks of clean reports.
8. Test: from a personal account, send to `rbailey@<domain>` and confirm it arrives at `rbailey@powerconnection.com`.

Mail sent to an address with no matching powerconnection.com user bounces. To catch those too: Gmail → **Routing → Default routing**, add a catch-all rule for the alias domains → your mailbox.

**Bonus, account recovery:** if you add `connectedenergyservices.com` as an alias domain the same way, `rbailey@connectedenergyservices.com` starts arriving in your powerconnection.com inbox. That makes the at-risk Notion login recoverable (you can receive its login codes). This only works if you control that domain's DNS.

## 2. Web: forward each domain to powerconnection.com
GoDaddy → My Products → the domain → **DNS → Forwarding** tab → **Add Forwarding** (domain):
- Destination: `https://` + `powerconnection.com` · Type **Permanent (301)** · Settings **Forward only** (not "with masking", which breaks SEO and HTTPS) → Save.
- Also forward the `www` subdomain: Forwarding → Add → Subdomain `www` → same settings.
- GoDaddy manages the A/CNAME records it needs for forwarding. Don't delete them afterwards, and leave the MX/TXT records from step 1 in place.
- Optional: keep brand context, e.g. `connectedsolar.com` → `https://powerconnection.com/solar`.

## 3. After
- ☐ Re-run `check_domains.sh`. The "after" snapshot should show MX = Google, SPF + DMARC present, and web = 301 to powerconnection.com.
- ☐ Update the platform register (T-03) and `docs/CLOUD-ARCHITECTURE.md` (L0 domains).
- ☐ Registrar hygiene: all domains in one GoDaddy account owned by the right entity, auto-renew on, account 2FA on, and the login stored in 1Password.
- ☐ Later: consider moving DNS to Cloudflare for one place to manage all domains (optional).
