#!/usr/bin/env python3
"""discover_accounts.py — find every platform/account a client uses, from browser history, bookmarks,
1Password item *titles/domains* (never secrets), Obsidian vault registry, macOS Internet Accounts and the Apple Mail index
(all mail accounts in Mail.app, e.g. iCloud, Gmail, Exchange). READ-ONLY; metadata only.

    python3 discover_accounts.py --out <dir>                                   # Obsidian registry only
    python3 discover_accounts.py --out <dir> --consent-4b                      # + browsers, bookmarks, 1Password titles
    python3 discover_accounts.py --out <dir> --consent-4b --mail-accounts a@x.com,b@y.com   # + those Mail accounts
Browsers, bookmarks, 1Password and Apple Mail are T-02 clause 4b sources: they are read only with --consent-4b.
Mail and Internet Accounts are further limited to the accounts listed in Schedule A (--mail-accounts; "all" = every account).

Writes to <dir>:
  platforms-detected.csv    platform, layer, evidence source, visit count, last seen, tenants/workspaces seen
  ai-projects.csv           AI project/GPT/Space/Gem/notebook URLs + titles (claude.ai, chatgpt.com, perplexity.ai, gemini, notebooklm, grok …)
  bookmarks.md              bookmarks grouped by folder (title + domain)
  1password-items.csv       vault, category, title, domain  (only if `op` is signed in)
  obsidian-vaults.md        vault paths + sizes
  mail-accounts.csv         every Mail.app account (username), message count, last received + macOS Internet Accounts
  mail-alerts.csv           registrar/billing/security/bounce alerts only: date, account, sender domain, subject
Privacy: full browsing history and search terms are NOT exported — only known-platform domains are counted, and page
titles are kept only for AI project-type URLs. Mail: sender domains are counted; subjects are kept only for alert-type
messages (expiry, renewal, parked, suspension, payment, sign-in, bounces). Bodies are never read.
Needs Terminal "Full Disk Access" for Safari and Mail. Chromium DBs are copied to a temp file first (browsers lock them).
"""
import argparse, csv, datetime, glob, json, os, plistlib, re, shutil, sqlite3, subprocess, sys, tempfile
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

HOME = Path.home()

# domain suffix → (platform, layer). Order: most specific first.
CATALOG = [
    ("claude.ai", "Claude", "L5-ai"), ("console.anthropic.com", "Anthropic API console", "L5-ai"), ("platform.claude.com", "Anthropic API console", "L5-ai"),
    ("chatgpt.com", "ChatGPT", "L5-ai"), ("chat.openai.com", "ChatGPT", "L5-ai"), ("platform.openai.com", "OpenAI API platform", "L5-ai"),
    ("grok.com", "Grok", "L5-ai"), ("console.x.ai", "xAI console", "L5-ai"), ("x.ai", "xAI", "L5-ai"),
    ("perplexity.ai", "Perplexity", "L5-ai"), ("gemini.google.com", "Gemini", "L5-ai"), ("notebooklm.google.com", "NotebookLM", "L5-ai"),
    ("aistudio.google.com", "Google AI Studio", "L5-ai"), ("copilot.microsoft.com", "Microsoft Copilot (consumer)", "L5-ai"),
    ("m365.cloud.microsoft", "Microsoft 365 Copilot", "L5-ai"), ("copilotstudio.microsoft.com", "Copilot Studio", "L5-ai"),
    ("cursor.com", "Cursor", "L3-code"), ("devin.ai", "Devin", "L3-code"), ("warp.dev", "Warp", "L3-code"), ("antigravity.google", "Google Antigravity", "L3-code"),
    ("openrouter.ai", "OpenRouter", "L5-ai"), ("groq.com", "Groq", "L5-ai"), ("huggingface.co", "Hugging Face", "L4-runtime"),
    ("replit.com", "Replit", "L3-code"), ("lovable.dev", "Lovable", "L3-code"), ("bolt.new", "Bolt", "L3-code"), ("v0.dev", "v0", "L3-code"), ("v0.app", "v0", "L3-code"),
    ("github.com", "GitHub", "L3-code"), ("gitlab.com", "GitLab", "L3-code"), ("bitbucket.org", "Bitbucket", "L3-code"),
    ("entra.microsoft.com", "Microsoft Entra ID", "L0-identity"), ("portal.azure.com", "Azure", "L1-cloud"), ("admin.microsoft.com", "Microsoft 365 admin", "L2-workspace"),
    ("sharepoint.com", "SharePoint / OneDrive", "L2-workspace"), ("onedrive.live.com", "OneDrive (consumer)", "L2-workspace"),
    ("outlook.office.com", "Outlook (M365)", "L2-workspace"), ("outlook.live.com", "Outlook.com (consumer)", "L2-workspace"),
    ("okta.com", "Okta", "L0-identity"), ("1password.com", "1Password", "L0-secrets"),
    ("console.cloud.google.com", "Google Cloud", "L1-cloud"), ("admin.google.com", "Google Workspace admin", "L2-workspace"),
    ("drive.google.com", "Google Drive", "L2-workspace"), ("mail.google.com", "Gmail", "L2-workspace"),
    ("icloud.com", "iCloud", "L2-workspace"), ("dropbox.com", "Dropbox", "L2-workspace"), ("box.com", "Box", "L2-workspace"),
    ("vercel.com", "Vercel", "L4-runtime"), ("vercel.app", "Vercel deployments", "L4-runtime"), ("cloudflare.com", "Cloudflare", "L4-runtime"),
    ("render.com", "Render", "L4-runtime"), ("railway.app", "Railway", "L4-runtime"), ("railway.com", "Railway", "L4-runtime"),
    ("netlify.com", "Netlify", "L4-runtime"), ("supabase.com", "Supabase", "L4-runtime"), ("neon.tech", "Neon", "L4-runtime"),
    ("firebase.google.com", "Firebase", "L4-runtime"), ("databricks.com", "Databricks", "L4-runtime"), ("aws.amazon.com", "AWS", "L1-cloud"),
    ("namecheap.com", "Namecheap (domains)", "L0-domains"), ("godaddy.com", "GoDaddy (domains)", "L0-domains"),
    ("squarespace.com", "Squarespace (domains/sites)", "L0-domains"), ("porkbun.com", "Porkbun (domains)", "L0-domains"),
    ("quickbooks.intuit.com", "QuickBooks Online", "L5-finance"), ("qbo.intuit.com", "QuickBooks Online", "L5-finance"), ("intuit.com", "Intuit", "L5-finance"),
    ("stripe.com", "Stripe", "L5-finance"), ("mercury.com", "Mercury", "L5-finance"), ("brex.com", "Brex", "L5-finance"), ("gusto.com", "Gusto", "L5-finance"),
    ("notion.so", "Notion", "L5-saas"), ("notion.com", "Notion", "L5-saas"), ("notion.site", "Notion public pages", "L5-saas"), ("obsidian.md", "Obsidian", "L5-saas"),
    ("slack.com", "Slack", "L5-saas"), ("linear.app", "Linear", "L5-saas"), ("atlassian.net", "Atlassian (Jira/Confluence)", "L5-saas"),
    ("hubspot.com", "HubSpot", "L5-saas"), ("attio.com", "Attio", "L5-saas"), ("airtable.com", "Airtable", "L5-saas"), ("salesforce.com", "Salesforce", "L5-saas"),
    ("zapier.com", "Zapier", "L5-automation"), ("make.com", "Make", "L5-automation"), ("n8n.cloud", "n8n", "L5-automation"),
    ("twilio.com", "Twilio", "L4-runtime"), ("docusign.net", "DocuSign", "L5-saas"), ("docusign.com", "DocuSign", "L5-saas"),
]
# subdomain patterns that reveal tenant/workspace names
TENANT_PATTERNS = [
    (re.compile(r"^([\w-]+?)(?:-my)?\.sharepoint\.com$"), "SharePoint / OneDrive"),
    (re.compile(r"^([\w-]+)\.slack\.com$"), "Slack"), (re.compile(r"^([\w-]+)\.atlassian\.net$"), "Atlassian (Jira/Confluence)"),
    (re.compile(r"^([\w-]+)\.notion\.site$"), "Notion public pages"), (re.compile(r"^([\w-]+)\.okta\.com$"), "Okta"),
    (re.compile(r"^([\w-]+)\.1password\.com$"), "1Password"), (re.compile(r"^([\w-]+)\.vercel\.app$"), "Vercel deployments"),
    (re.compile(r"^([\w-]+)\.my\.salesforce\.com$"), "Salesforce"), (re.compile(r"^([\w-]+)\.cloud\.databricks\.com$"), "Databricks"),
]
# host → path prefixes that identify an AI project, GPT, Space, Gem or notebook
AI_PROJECT_PATHS = {
    "claude.ai": ("/project/",), "chatgpt.com": ("/g/", "/gpts", "/project"), "perplexity.ai": ("/spaces/", "/collections/", "/page/"),
    "gemini.google.com": ("/gem/",), "notebooklm.google.com": ("/notebook/",), "grok.com": ("/project",),
    "aistudio.google.com": ("/prompts/",),  # Copilot Studio left out until its agent URL pattern is verified
}


def is_ai_project(url):
    u = urlparse(url or "")
    host = (u.hostname or "").lower()
    host = host[4:] if host.startswith("www.") else host
    return u.scheme in ("http", "https") and any(u.path.startswith(p) for p in AI_PROJECT_PATHS.get(host, ()))

CHROMIUM = {
    "Chrome": HOME / "Library/Application Support/Google/Chrome",
    "Edge": HOME / "Library/Application Support/Microsoft Edge",
    "Brave": HOME / "Library/Application Support/BraveSoftware/Brave-Browser",
    "Arc": HOME / "Library/Application Support/Arc/User Data",
    "Comet": HOME / "Library/Application Support/Comet",
}


def classify(host):
    host = (host or "").lower().lstrip(".")
    if host.startswith("www."):
        host = host[4:]
    for suffix, name, layer in CATALOG:
        if host == suffix or host.endswith("." + suffix):
            return name, layer
    return None


def tenant_of(host):
    for pat, name in TENANT_PATTERNS:
        m = pat.match((host or "").lower())
        if m and m.group(1) not in ("www", "app", "login", "my"):
            return name, m.group(1)
    return None


def read_sqlite(path, query, required=False):
    """Rows, or [] if the database can't be read. required=True raises instead, for sources a report can't skip."""
    tmp = Path(tempfile.mkdtemp()) / "db"
    try:
        shutil.copy2(path, tmp)
        for ext in ("-wal", "-shm"):
            if Path(str(path) + ext).exists():
                shutil.copy2(str(path) + ext, str(tmp) + ext)
        con = sqlite3.connect(f"file:{tmp}?mode=ro", uri=True)
        rows = con.execute(query).fetchall()
        con.close()
        return rows
    except Exception as e:  # locked, permission (needs Full Disk Access), schema change
        print(f"  skip {path}: {e}")
        if required:
            raise
        return []
    finally:
        shutil.rmtree(tmp.parent, ignore_errors=True)


def history_rows():
    """yield (browser, url, title, visit_count, last_visit_datetime)"""
    for browser, root in CHROMIUM.items():
        for h in glob.glob(str(root / "*" / "History")) + glob.glob(str(root / "History")):
            profile = Path(h).parent.name
            for url, title, cnt, t in read_sqlite(h, "SELECT url, title, visit_count, last_visit_time FROM urls"):
                ts = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=t or 0)
                yield f"{browser}:{profile}", url, title, cnt or 0, ts
    safari = HOME / "Library/Safari/History.db"
    if safari.exists():
        q = ("SELECT i.url, v.title, i.visit_count, MAX(v.visit_time) FROM history_items i "
             "LEFT JOIN history_visits v ON v.history_item = i.id GROUP BY i.id")
        for url, title, cnt, t in read_sqlite(safari, q):
            ts = datetime.datetime(2001, 1, 1) + datetime.timedelta(seconds=t or 0)
            yield "Safari", url, title, cnt or 0, ts


def bookmark_rows():
    """yield (browser, folder, title, url)"""
    def walk(node, path, browser):
        if node.get("type") == "url":
            yield browser, path, node.get("name", ""), node.get("url", "")
        for c in node.get("children", []) or []:
            yield from walk(c, f"{path}/{node.get('name', '')}".strip("/") if node.get("type") == "folder" else path, browser)
    for browser, root in CHROMIUM.items():
        for b in glob.glob(str(root / "*" / "Bookmarks")) + glob.glob(str(root / "Bookmarks")):
            try:
                data = json.load(open(b))
                for rootnode in data.get("roots", {}).values():
                    if isinstance(rootnode, dict):
                        yield from walk(rootnode, "", browser)
            except Exception as e:
                print(f"  skip {b}: {e}")
    plist = HOME / "Library/Safari/Bookmarks.plist"
    if plist.exists():
        def swalk(node, path):
            if node.get("WebBookmarkType") == "WebBookmarkTypeLeaf":
                yield "Safari", path, (node.get("URIDictionary") or {}).get("title", ""), node.get("URLString", "")
            for c in node.get("Children", []) or []:
                yield from swalk(c, f"{path}/{node.get('Title', '')}".strip("/"))
        try:
            yield from swalk(plistlib.load(open(plist, "rb")), "")
        except Exception as e:
            print(f"  skip Safari bookmarks: {e}")


ALERT = re.compile(r"expir|renew|parked|suspen|cancel|past due|payment (fail|declin|problem)|update (your )?payment|"
                   r"delivery status|undeliverable|not delivered|mail delivery|security alert|new sign.?in|password reset|"
                   r"verify your|unusual activity|domain", re.I)


def mail_accounts_map():
    """account identifier (UUID) → (username, type) from macOS Internet Accounts."""
    out = {}
    db = HOME / "Library/Accounts/Accounts4.sqlite"
    if db.exists():
        q = ("SELECT a.ZIDENTIFIER, a.ZUSERNAME, a.ZACCOUNTDESCRIPTION, t.ZACCOUNTTYPEDESCRIPTION FROM ZACCOUNT a "
             "LEFT JOIN ZACCOUNTTYPE t ON a.ZACCOUNTTYPE = t.Z_PK")
        for ident, user, desc, typ in read_sqlite(db, q):
            out[ident] = (user or desc or "", typ or "")
    return out


def in_scope(user, allowed):
    return allowed is None or (user or "").lower() in allowed


def apple_mail(hit, allowed):
    """Metadata from Mail.app's Envelope Index: accounts, platform senders, alert subjects. allowed=None means all accounts.
    Returns (account rows, alerts, accounts map, unresolved mailbox ids, read_failed)."""
    idx = sorted(glob.glob(str(HOME / "Library/Mail/V*/MailData/Envelope Index")),
                 key=lambda p: int(re.search(r"/V(\d+)/", p).group(1)) if re.search(r"/V(\d+)/", p) else 0)
    accounts = mail_accounts_map()
    acct_rows, alerts, unresolved = {}, [], set()
    if not idx:
        print("  Apple Mail: no Envelope Index (Mail not used, or Terminal lacks Full Disk Access)")
        return acct_rows, alerts, accounts, unresolved, False
    q = ("SELECT mb.url, a.address, s.subject, m.date_received FROM messages m "
         "JOIN mailboxes mb ON m.mailbox = mb.ROWID LEFT JOIN addresses a ON m.sender = a.ROWID "
         "LEFT JOIN subjects s ON m.subject = s.ROWID")
    try:
        messages = read_sqlite(idx[-1], q, required=True)
    except Exception:
        return acct_rows, alerts, accounts, unresolved, True
    for url, sender, subject, received in messages:
        acct_id = urlparse(url or "").netloc
        if allowed is not None and acct_id not in accounts:
            unresolved.add(acct_id)  # can't tell whose mailbox this is, so it can't be matched to Schedule A
            continue
        user = accounts.get(acct_id, (acct_id, ""))[0] or acct_id
        if not in_scope(user, allowed):
            continue
        ts = datetime.datetime.fromtimestamp(received or 0)
        r = acct_rows.setdefault(user, {"messages": 0, "last": ts, "type": accounts.get(acct_id, ("", ""))[1]})
        r["messages"] += 1
        r["last"] = max(r["last"], ts)
        domain = (sender or "").rsplit("@", 1)[-1].lower().strip(">")
        c = classify(domain)
        if c:
            hit(c[0], c[1], "Apple Mail sender", 1, ts)
        is_bounce = domain.startswith(("mailer-daemon", "postmaster")) or (sender or "").lower().startswith(("mailer-daemon", "postmaster"))
        if (c or is_bounce) and subject and ALERT.search(subject):
            alerts.append([ts.strftime("%Y-%m-%d"), user, domain, subject[:160]])
    return acct_rows, alerts, accounts, unresolved, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--consent-4b", action="store_true", help="T-02 clause 4b is ticked: read browsers, bookmarks, 1Password titles, Mail")
    ap.add_argument("--mail-accounts", default="", help='comma-separated Schedule A mail accounts, or "all"; empty = skip Mail')
    a = ap.parse_args()
    os.umask(0o077)
    a.out.mkdir(parents=True, exist_ok=True)
    mail_allowed = None if a.mail_accounts.strip().lower() == "all" else {m.strip().lower() for m in a.mail_accounts.split(",") if m.strip()}
    if not a.consent_4b:
        print("  clause 4b not consented: skipping browsers, bookmarks, 1Password and Apple Mail")

    plat = defaultdict(lambda: {"layer": "", "sources": set(), "visits": 0, "last": None, "tenants": set()})
    projects = {}

    def hit(name, layer, source, visits=0, last=None, tenant=None):
        p = plat[name]
        p["layer"] = layer
        p["sources"].add(source)
        p["visits"] += visits
        if last and (p["last"] is None or last > p["last"]):
            p["last"] = last
        if tenant:
            p["tenants"].add(tenant)

    for browser, url, title, cnt, ts in (history_rows() if a.consent_4b else ()):
        host = urlparse(url).hostname
        c = classify(host)
        t = tenant_of(host)
        if c:
            hit(c[0], c[1], browser.split(":")[0] + " history", cnt, ts, t[1] if t else None)
        elif t:
            hit(t[0], "L5-saas", browser.split(":")[0] + " history", cnt, ts, t[1])
        if is_ai_project(url):
            key = url.split("?")[0]
            if key not in projects or ts > projects[key][3]:
                projects[key] = (classify(host)[0] if classify(host) else host, title or "", browser, ts)

    bm_lines, n_bm = defaultdict(list), 0
    for browser, folder, title, url in (bookmark_rows() if a.consent_4b else ()):
        host = urlparse(url).hostname or ""
        n_bm += 1
        bm_lines[f"{browser} · {folder or '(root)'}"].append(f"- {title or host} — `{host}`")
        c = classify(host)
        if c:
            hit(c[0], c[1], f"{browser} bookmarks", tenant=(tenant_of(host) or (None, None))[1])

    # 1Password: titles + domains only
    op_rows = []
    if a.consent_4b and shutil.which("op"):
        try:
            items = json.loads(subprocess.run(["op", "item", "list", "--format", "json"], capture_output=True, text=True, timeout=120).stdout or "[]")
            for it in items:
                urls = [u.get("href", "") for u in (it.get("urls") or [])]
                host = urlparse(urls[0]).hostname if urls else ""
                op_rows.append([it.get("vault", {}).get("name", ""), it.get("category", ""), it.get("title", ""), host or ""])
                c = classify(host)
                if c:
                    hit(c[0], c[1], "1Password item", tenant=(tenant_of(host) or (None, None))[1])
        except Exception as e:
            print(f"  skip 1Password: {e} (sign in with `op signin`)")

    mail_rows, mail_alerts, sys_accounts, unresolved, mail_failed = {}, [], {}, set(), False
    if a.consent_4b and (mail_allowed is None or mail_allowed):
        mail_rows, mail_alerts, sys_accounts, unresolved, mail_failed = apple_mail(hit, mail_allowed)
    elif a.consent_4b:
        print("  Apple Mail: no --mail-accounts given (Schedule A), skipped")

    # Obsidian vault registry
    obs = HOME / "Library/Application Support/obsidian/obsidian.json"
    vault_md = ["# Obsidian vaults", ""]
    if obs.exists():
        try:
            for v in json.load(open(obs)).get("vaults", {}).values():
                p = Path(v.get("path", ""))
                size = subprocess.run(["du", "-sh", str(p)], capture_output=True, text=True).stdout.split("\t")[0] if p.exists() else "missing"
                vault_md.append(f"- `{p}` · {size}")
                hit("Obsidian", "L5-saas", "Obsidian vault registry")
        except Exception as e:
            vault_md.append(f"_could not read registry: {e}_")
    else:
        vault_md.append("_no Obsidian registry found_")

    with open(a.out / "platforms-detected.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["platform", "layer", "evidence", "visits", "last_seen", "tenants_or_workspaces"])
        for name, p in sorted(plat.items(), key=lambda kv: (kv[1]["layer"], -kv[1]["visits"])):
            w.writerow([name, p["layer"], "; ".join(sorted(p["sources"])), p["visits"],
                        p["last"].strftime("%Y-%m-%d") if p["last"] else "", "; ".join(sorted(p["tenants"]))])
    with open(a.out / "ai-projects.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tool", "title", "url", "browser", "last_seen"])
        for url, (tool, title, browser, ts) in sorted(projects.items(), key=lambda kv: kv[1][0]):
            w.writerow([tool, title, url, browser.split(":")[0], ts.strftime("%Y-%m-%d")])
    with open(a.out / "bookmarks.md", "w") as f:
        f.write(f"# Bookmarks ({n_bm})\n\n")
        for k in sorted(bm_lines):
            f.write(f"## {k}\n\n" + "\n".join(bm_lines[k]) + "\n\n")
    if op_rows:
        with open(a.out / "1password-items.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["vault", "category", "title", "domain"])
            w.writerows(sorted(op_rows))
    (a.out / "obsidian-vaults.md").write_text("\n".join(vault_md) + "\n")
    with open(a.out / "mail-accounts.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source", "account", "type", "messages", "last_received"])
        for user, r in sorted(mail_rows.items()):
            w.writerow(["Apple Mail", user, r["type"], r["messages"], r["last"].strftime("%Y-%m-%d")])
        for user, typ in sorted(set(sys_accounts.values())):
            if user and in_scope(user, mail_allowed):
                w.writerow(["macOS Internet Accounts", user, typ, "", ""])
    with open(a.out / "mail-alerts.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "account", "sender_domain", "subject"])
        w.writerows(sorted(mail_alerts, reverse=True))
    print(f"  mail accounts: {len(mail_rows)} · mail alerts: {len(mail_alerts)}")
    print(f"  platforms: {len(plat)} · AI projects: {len(projects)} · bookmarks: {n_bm} · 1Password items: {len(op_rows)}")
    # the caller marks the bundle incomplete on a non-zero exit
    if mail_failed:
        print("  ⚠ Apple Mail: the Envelope Index could not be read, so NO mail was checked against Schedule A. "
              "Grant Terminal Full Disk Access (or quit Mail) and re-run.")
    if unresolved:
        print(f"  ⚠ Apple Mail: {len(unresolved)} mailbox account(s) could not be identified (macOS Internet Accounts unreadable?), "
              "so their messages were NOT checked against Schedule A. Grant Full Disk Access and re-run.")
    if mail_failed or unresolved:
        sys.exit(3)


if __name__ == "__main__":
    main()
