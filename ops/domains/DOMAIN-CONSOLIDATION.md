# Point legacy domains at powerconnection.com (GoDaddy + Google Workspace)

Goal: `connectedsolar.com`, `getconnectedenergy.com`, `netzerolending.io`, `baileyco.us` (and optionally `connectedenergyservices.com`)
→ **web** redirects to https://powerconnection.com and **email** to any address @those domains lands in the matching @powerconnection.com inbox.

## 0. Pre-flight (do not skip: these domains may still carry live mail or legal evidence)
Run `bash ops/domains/check_domains.sh` on the Mac and record the output (the "before" snapshot) in the platform register.

| If the check shows… | Then |
|---|---|
| **MX → Microsoft 365** (likely for `netzerolending.io`, which has its own tenant) | That tenant owns the domain's mail, and its addresses must keep receiving until the MX change. In order: (1) **export mailboxes** (Purview); (2) **prepare Google first**: finish step 1.1–1.3 (Google verified, alias domain added) and step 1.8 (every live address has a user, group or routing rule), and decide where each live address should now receive mail; (3) **move sign-ins off the domain, not mail**: change users' sign-in names (UPNs) and admin accounts to another verified domain in that tenant, and set each mailbox's *primary* address to that domain, but **keep every old-domain address on its mailbox, shared mailbox and group as an alias**, so mail still arrives while MX points to Microsoft 365; (4) a day ahead, lower the MX record's TTL (e.g. 300 s) so cached Microsoft MX records expire quickly; (5) **cut over, in one sitting, at a quiet hour**: remove the old-domain aliases (Microsoft 365 refuses to remove a domain that is still in use), remove the domain (M365 admin → Settings → Domains → Remove), **immediately** switch MX to Google (step 1.4), and run the step 1.9 tests. Mail from senders still holding the old MX record (up to the lowered TTL) can bounce in that window; resend-check anything important. Skipping steps breaks sign-ins or mail silently |
| **MX → Google (another Workspace)** | Remove the domain from that Workspace first. A domain can belong to only one Google Workspace |
| **MX → GoDaddy / other with existing mailboxes** (e.g. old staff addresses on `getconnectedenergy.com`) | Export those mailboxes first. They may be **litigation evidence**: check with counsel about preservation before changing MX |
| **NS not GoDaddy** (e.g. Cloudflare) | Make **every** DNS change (TXT, MX, SPF, DKIM, DMARC) **and the web redirect** at that DNS host, not in GoDaddy. Do **not** use GoDaddy Forwarding for this domain: turning it on switches the nameservers back to GoDaddy and replaces the active DNS zone, which breaks mail and anything else hosted there (see step 2) |
| **Other services send mail as this domain** (SPF includes other senders, e.g. Mailchimp, HubSpot, QuickBooks, Stripe, a CRM) | List every sender from the current SPF record and the sending apps you know of. You'll keep them in step 1.5 |
| **Addresses other than yours receive mail** (e.g. `info@`, `sales@`, former staff) | List them now. Each needs a routing decision in step 1.8, because an alias domain only covers addresses that match an existing powerconnection.com user |
| Expiry soon / auto-renew off | Turn on auto-renew in GoDaddy now |

## 1. Email: add each domain as a *user alias domain* in Google Workspace
Result: `anyone@connectedsolar.com` is delivered to `anyone@powerconnection.com` for every existing user, at no extra license cost.

1. admin.google.com (as a powerconnection.com super admin) → **Account → Domains → Manage domains → Add a domain**.
2. Enter the domain → choose **User alias domain** → Add and start verification.
All records in steps 3–7 go in the domain's **authoritative DNS host** from step 0: GoDaddy (My Products → the domain → **DNS**)
only when the nameservers are `*.domaincontrol.com`; otherwise that host's zone (e.g. Cloudflare → the domain → **DNS → Records**).
Records added in GoDaddy DNS while the nameservers point elsewhere have no effect.

3. Google shows a **TXT verification record** → in the DNS host, add record: Type `TXT`, Name `@`, Value = Google's string → Save → back in Google click **Verify**. It usually works within minutes, but can take up to 48 hours.
4. **Activate Gmail** for the alias domain: in the DNS host, delete the existing MX records and add Google's MX record: Type `MX`, Name `@`, Value `smtp.google.com`, Priority `1`.
   (If Google's setup screen shows a different set, e.g. the 5 older `aspmx.l.google.com` records, use exactly what it shows.)
5. **SPF:** a domain has exactly **one** SPF TXT record on `@`. Build it from the sender list in step 0: start from `v=spf1 include:_spf.google.com`, add each other active sender's mechanism (e.g. `include:servers.mcsv.net` for Mailchimp, whatever each vendor documents), then end with `~all`. Use the Google-only value `v=spf1 include:_spf.google.com ~all` **only if Google Workspace is the sole sender**. Dropping a sender's include makes its mail fail authentication.
6. **DKIM:** admin.google.com → Apps → Google Workspace → Gmail → **Authenticate email** → select the domain → Generate new record → add the `google._domainkey` TXT in the DNS host → **Start authentication**.
7. **DMARC:** TXT, Name `_dmarc`, Value `v=DMARC1; p=none; rua=mailto:rbailey@powerconnection.com`. Move to `p=quarantine` after 2–4 weeks of clean reports.
8. **Route addresses that have no matching user** (part of the migration, not optional): for each address from the step-0 list decide *keep* (create a powerconnection.com user or group with that name, e.g. `info@` → a Google Group), *forward* (Gmail → **Routing → Default routing** → a rule for the alias domain that delivers unmatched recipients to a chosen mailbox), or *let bounce* (only for addresses you are sure are dead). Record each decision in the platform register.
9. **Test before calling it done:** from a personal account, send to `rbailey@<domain>` (must arrive at `rbailey@powerconnection.com`)
   and to **one address for each routing decision from step 8** (each kept address reaches its user or group; each forwarded one
   reaches its mailbox). Send to an arbitrary address such as `test-unmatched@<domain>` **only if you configured a catch-all rule**:
   it must then reach the catch-all mailbox. Without a catch-all, a bounce for that arbitrary address is the correct result.

**Bonus, account recovery:** if you add `connectedenergyservices.com` as an alias domain the same way, `rbailey@connectedenergyservices.com` starts arriving in your powerconnection.com inbox. That makes the at-risk Notion login recoverable (you can receive its login codes). This only works if you control that domain's DNS.

## 2. Web: forward each domain to powerconnection.com
**Where to do it depends on the nameservers from step 0.** GoDaddy Forwarding only works on GoDaddy DNS: enabling it on a domain whose nameservers point elsewhere switches them back to GoDaddy and replaces the live DNS zone.

**A. Nameservers are GoDaddy (`*.domaincontrol.com`):** GoDaddy → My Products → the domain → **DNS → Forwarding** tab → **Add Forwarding** (domain):
- Destination: `https://` + `powerconnection.com` · Type **Permanent (301)** · Settings **Forward only** (not "with masking", which breaks SEO and HTTPS) → Save.
- Also forward the `www` subdomain: Forwarding → Add → Subdomain `www` → same settings.
- GoDaddy manages the A/CNAME records it needs for forwarding. Don't delete them afterwards, and leave the MX/TXT records from step 1 in place.
- Optional: keep brand context, e.g. `connectedsolar.com` → `https://powerconnection.com/solar`.

**B. Nameservers are elsewhere (e.g. Cloudflare):** leave GoDaddy Forwarding **off** and redirect at that DNS host, keeping its zone and records as they are. On Cloudflare: make sure the apex and `www` have proxied (orange-cloud) records (a placeholder `A 192.0.2.1` proxied record is fine if nothing else serves the site), then **Rules → Redirect Rules** → Create rule → **Custom filter expression**: *Hostname* equals `<domain>` **or** *Hostname* equals `www.<domain>`
(not "All incoming requests", which would also redirect any API or other subdomain in the zone) → **Static** redirect to
`https://powerconnection.com` with status **301** (preserve query string on). Other hosts have an equivalent "URL redirect" feature; use theirs.

## 3. After
- ☐ Re-run `check_domains.sh`. The "after" snapshot should show MX = Google, one SPF record that still includes every active sender, DMARC present, and `http://`, `https://` and `https://www.` all redirecting (301) to powerconnection.com with no request errors.
- ☐ Update the platform register (T-03) and `docs/CLOUD-ARCHITECTURE.md` (L0 domains).
- ☐ Registrar hygiene: all domains in one GoDaddy account owned by the right entity, auto-renew on, account 2FA on, and the login stored in 1Password.
- ☐ Later: consider moving DNS to Cloudflare for one place to manage all domains (optional).
