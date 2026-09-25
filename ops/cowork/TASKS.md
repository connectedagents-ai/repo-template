# Cowork task scripts: paste one at a time into Claude Cowork on your Mac

Claude Cowork (in the Claude desktop app) works on your Mac with you watching. It uses the browser through **Claude in
Chrome** (https://claude.ai/chrome) and Terminal commands. It stops and asks whenever something needs your approval, a
login or a 2FA code. Paste the **ground rules** first, then one task at a time. Each task ends with a short report you can
paste back into any Claude chat.

## Option: Claude Code driving your own Edge and Chrome
If you'd rather use Claude Code in Terminal (reachable from your phone) with Edge and Chrome, run once:
```bash
cd ~/Code/repo-template && git pull && bash ops/cowork/connect_browsers.sh
```
It opens Edge and Chrome in their own windows, connected to Claude Code. Sign in to GitHub and Google there once (the
logins stay). Then start `claude remote-control` in the same folder and paste the ground rules and tasks below.

## Ground rules (paste first, once per Cowork session)
```
You are working on my Mac with me watching. Rules for everything I ask today:
- Stop and ask me before anything that deletes, revokes, archives, pays, sends or publishes. Show me exactly what you will do first.
- I type every password, 2FA code and passkey myself. When a login or approval appears, stop and tell me.
- Never copy large data onto the Mac's internal disk. Backups and reports go on "/Volumes/Extreme SSD". If the SSD is not mounted, stop.
- My code repo is ~/Code/repo-template. Read its AGENTS.md before running anything from it. Run `git pull` there first.
- Use the gh CLI in Terminal for GitHub when you can; use Chrome for pages that need clicking.
- After each task, give me a short report: what ran, what passed, what failed, what you skipped.
```

## Task 1: back up Connected-Energy-AI to the SSD (10–30 min, read-only on GitHub)
```
Run this in Terminal and show me the last line:
DEST="/Volumes/Extreme SSD/github-backup/Connected-Energy-AI"; mkdir -p "$DEST" && cd "$DEST" || exit 1
gh repo list Connected-Energy-AI --limit 500 --json name -q '.[].name' | while read -r r; do
  if [ -d "$r.git" ]; then git -C "$r.git" remote update --prune; else gh repo clone "Connected-Energy-AI/$r" "$r.git" -- --mirror; fi
done
echo "Backed up: $(ls -d *.git | wc -l | tr -d ' ') repos, $(du -sh . | cut -f1)"
It should say about 80 repos. If gh asks me to log in, stop and tell me.
```

## Task 2: delete the 16 attacker branches (needs Task 1 done)
```
Each branch below was created by the attacker on 2026-05-18 and holds only one attacker commit (a file named
.github/workflows/megalodon.yml). For each one: check with
  gh api repos/Connected-Energy-AI/<repo>/compare/HEAD...<branch> -q '[.ahead_by, (.files|map(.filename)|join(","))]|@tsv'
that it is 1 commit ahead and only changes .github/workflows/megalodon.yml. Show me the table, wait for my OK, then delete with
  gh api -X DELETE repos/Connected-Energy-AI/<repo>/git/refs/heads/<branch>
Skip and report any branch that doesn't match.
AI-Generated-Agents mega-lwn5lhb2
CURSOR-CLOUD-AGENTS mega-cxez4uf8
Litigation-Force-Interactive-Presentation mega-r6sbyfbc
Powermed-Marketing mega-qyudzn72
agent-skills-suite-v2 mega-trg9ox63
connected-agents-ai mega-q6h4boa8
empathic-voice-interface-starter mega-cvrhc6uv
energy-navigator-ai mega-2zfzref6
file-management-toolkit mega-j9nzr3uv
onewish-os mega-twkni8py
powerconnectionai mega-umfkc86n
powermedmarkeetingai-v0-modern-website-design mega-ujq4ci3y
smithwick-ai-demo mega-a1pn71u4
tesla-energy-battlecards mega-a8fmnvl9
twinkle-tale-lab-v2 mega-a531t8ge
voiceagent.ai mega-ydpt7e9d
```

## Task 3: find how the attacker got in (read-only)
```
In Chrome, open these two pages and read every entry from 2026-05-18 between 13:00 and 13:45 UTC:
1. https://github.com/settings/security-log?q=created%3A2026-05-18
2. https://github.com/organizations/Connected-Energy-AI/settings/audit-log?q=created%3A2026-05-18
   (if empty: "Switch settings context" at the top right → the "Connected Energy.AI" enterprise → Audit log, same search)
For each event, write down: time, action, actor, and the token / OAuth app / programmatic access type and IP it shows.
Tell me which app, token or SSH key pushed the changes. Don't revoke anything; just report.
```

## Task 4: review app access, keep what I use (no mass revoke)
```
Open https://github.com/settings/applications (Authorized OAuth Apps, about 154 apps). I want to KEEP my apps.
Make me a table of every app: name, owner, last used, and flag it if:
  - the owner is not the company's real GitHub account (for example "Microsoft-Corporation" owned by Microsoft-corp,
    "Microsoft Events" owned by MicrsoftEvents1, "Qwen" owned by liuyhwangyh, "Zencoder" owned by forgoodaigithub), or
  - it matches the app Task 3 found.
Show me only the flagged ones and ask which to revoke. Revoke only the ones I name.
Then do the same for https://github.com/settings/apps/authorizations and https://github.com/settings/installations.
```

## Task 5: clean the 10 infected working branches
```
These branches contain a workflow with the attacker's code (a line with "base64 -d | bash" or "216.126.225.129").
For each: show me the infected file and the commit that changed it, then propose the fix (delete the file if the attacker
added it, or restore the version from before 2026-05-18 if the attacker overwrote it). Wait for my OK, then commit
"fix(security): remove credential-stealing workflow from 2026-05-18" to that branch only. Keep all my other work.
LitigationForce.AI: claude/social-agent-orchestration-01M3dnJtXVuFhheEExQDnViE, codex/openai-capability-registry,
  dependabot/github_actions/actions/checkout-6, feat/wave-1b-dual-lane-finalize (.github/workflows/release.yml)
CURSOR-CLOUD-AGENTS: copilot/build-chairman-agent-orchestration-system, copilot/build-devdocs-scraper-system-again,
  cursor/setup-dev-environment-ec17, feat/ercot-bill-ingestion (.github/workflows/linear-buildout-scheduled.yml)
agent-skills-suite-v2: cursor/nldts-notion-provisioning-cda6 (.github/workflows/ci.yml)
Also LitigationForce.AI main: .github/workflows/release.yml. Ask me: delete it, or restore the pre-attack version.
```

## Task 6: scan the rest (read-only)
```
cd ~/Code/repo-template && git pull && bash ops/security/scan_infected_repos.sh Connected-Energy-AI connectedagents-ai
Show me the output. Any repo it lists that is not archived: tell me the file and branch.
```

## Task 7: free SSD space (preview, then my OK)
```
cd ~/Code/repo-template && bash ops/dedup/ssd_dedup.sh
Show me the summary (how many files, how many GB, and 10 sample pairs). Wait for my OK, then run the --apply command it
prints. Legal-flagged files are never touched. Tell me where restore.sh was written.
```

## Task 8: finish the new org (needs my approval to pay)
```
1. Open https://github.com/organizations/powerconnectionai/settings/billing/plans and show me the Team plan price.
   I click Upgrade and pay myself.
2. Then run: cd ~/Code/repo-template && bash ops/github-setup/configure_github.sh --apply powerconnectionai
   Show me every FAIL line.
3. Open https://github.com/connectedagents-ai/repo-template/compare/main...claude/code-chairman-repo-org-ocoe3d and
   create the pull request titled "chore: rules, ops tools and security scan". I review and merge it.
```
