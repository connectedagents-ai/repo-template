# Claude app reset: review and clean the old setup

Covers the Claude Desktop app and claude.ai account (chats, projects, artifacts, scheduled tasks, skills, connectors,
plugins, extensions, memory). The file-level cleanup is `archive_claude_files.sh`. This checklist is everything that lives in the
app and account. **Export first, then clean.** Nothing here can be undone once deleted.

## 0. Decide the account (once)
- ☐ Which Claude login is canonical? Check under your name at the bottom left (e.g. "Robert · Max"). If you have more than one Claude account, pick one
  to keep. Export the others (step 1), then cancel their plans.
- ☐ Settings → Account: confirm the email, and that the plan is billed to the right entity.

## 1. Export before touching anything
- ☐ Settings → Privacy → **Export data** (you get a zip by email) → `python3 ops/ai-library/ingest_library.py --source claude --account <label> <zip> --apply`.
- ☐ Projects: copy each project's **instructions** into `ai-library/prompts/claude/<project>.md`, and download its knowledge files.
- ☐ Artifacts: open the ones worth keeping, then download or publish them into the library.

## 2. Fix the error banner ("MCP desktop-automation: Server disconnected")
- ☐ Quit Claude → `bash ops/mac-cleanup/archive_claude_files.sh --apply --prune-mcp` → reopen.
  This removes `desktop-automation` and the other legacy servers, with a backup and an undo script.
  Manual alternative: Settings → Developer → **Edit config**, delete the `desktop-automation` block, save, and restart.

## 3. Extensions (Settings → Extensions, or Directory)
| Keep if used | Remove |
|---|---|
| Filesystem, Desktop Commander, pdf-viewer (it works and is useful for PDFs and forms) | Control Chrome (replaced by the built-in Claude in Chrome), Read and Send iMessages (unless you use it), anything you don't recognize |
- ☐ For each kept extension, open **Configure** and check that its folder or permission scope is as narrow as possible (e.g. Filesystem only on `~/Code` and the document vault, not `/`).

## 4. Customize: skills, connectors, plugins
- ☐ **Skills:** disable duplicates and beginner experiments. The keepers move into `ai-library/skills/` and get reinstalled from there.
- ☐ **Connectors:** keep one per service and account (Google Drive/Gmail/Calendar, Microsoft 365, GitHub, Notion). Disconnect stale or duplicate accounts.
  Connect the missing ones you want crawled (other Microsoft 365 tenants, Dropbox).
- ☐ **Plugins:** remove unused ones.

## 5. Chats, projects, scheduled tasks
- ☐ **Chats and tasks:** after the export, delete the throwaway chats ("Test", trip planning, and the like) and keep the working ones.
  Rename kept chats per `docs/NAMING-CONVENTIONS.md`.
- ☐ **Projects:** one project per real domain or product (matching the GitHub repos). Merge or delete old ones.
- ☐ **Scheduled:** review every scheduled task. Delete the obsolete ones. Keepers get a clear name and owner.
- ☐ **Artifacts:** delete drafts and duplicates. Name the keepers properly.

## 6. Memory and instructions
- ☐ Settings → **Memory**: read what's stored. Delete wrong or outdated entries, and add the durable preferences you want (e.g. the canonical GitHub org, naming rules).
- ☐ Settings → General → personal preferences / instructions: replace the beginner text with the short global rules (`templates/CLAUDE.md`).
- ☐ Claude Code on the Mac: `~/.claude/CLAUDE.md` + `settings.json` from `templates/`.

## 7. Verify
- ☐ Relaunch Claude Desktop: no error banners, and Developer shows only the kept servers, all running.
- ☐ Ask Claude: "list your connected tools". It should match what you kept.
- ☐ Record the date in the platform register (T-03) row for Claude.
