#!/usr/bin/env python3
"""park_mcp_servers.py — keep a core set of MCP servers in an AI tool's config and park the rest (reversible).

Supports Codex (~/.codex/config.toml, [mcp_servers.<name>] tables) and any JSON config with an "mcpServers" object
(Grok CLI ~/.grok/user-settings.json or .grok/settings.json, Claude Desktop, Cursor ~/.cursor/mcp.json, Gemini ~/.gemini/settings.json).

    python3 park_mcp_servers.py --config ~/.codex/config.toml --keep-file ops/mcp/core-servers.txt           # DRY RUN
    python3 park_mcp_servers.py --config ~/.codex/config.toml --keep-file ops/mcp/core-servers.txt --apply
    python3 park_mcp_servers.py --config ~/.grok/user-settings.json --keep github,filesystem --apply

--apply: backs up the config (<config>.bak-<stamp>), moves non-core servers into a sibling parked file
(mcp.parked.toml / mcp.parked.json, merged if it exists), and rewrites the config with only the core servers.
Restore = copy the backup back. Also reports inline secrets (names only) in kept servers so they can move to op:// refs,
and top-level API keys in the file (e.g. Grok CLI "apiKey").
"""
import argparse, datetime, json, re, shutil, sys
from pathlib import Path

SECRET = re.compile(r"KEY|TOKEN|SECRET|PASSWORD", re.I)


def toml_blocks(text):
    """Split Codex TOML into (preamble, {server: block_text}, trailer_blocks) by [mcp_servers.<name>...] headers."""
    lines = text.splitlines(keepends=True)
    out, servers, current, buf = [], {}, None, []
    header = re.compile(r'^\s*\[\s*mcp_servers\.("([^"]+)"|[A-Za-z0-9_-]+)')
    other = re.compile(r"^\s*\[")
    for ln in lines:
        m = header.match(ln)
        if m:
            name = m.group(2) or m.group(1)
            if current is not None:
                servers.setdefault(current, []).extend(buf)
            elif buf:
                out.extend(buf)
            current, buf = name, [ln]
        elif other.match(ln):
            if current is not None:
                servers.setdefault(current, []).extend(buf)
            else:
                out.extend(buf)
            current, buf = None, [ln]
        else:
            buf.append(ln)
    if current is not None:
        servers.setdefault(current, []).extend(buf)
    else:
        out.extend(buf)
    return "".join(out), {k: "".join(v) for k, v in servers.items()}


def inline_secrets_toml(block):
    return sorted({k for k, v in re.findall(r'([A-Za-z0-9_]+)\s*=\s*"([^"]*)"', block)
                   if SECRET.search(k) and v and not v.startswith("op://")})


def inline_secrets_json(server):
    env = (server or {}).get("env") or {}
    return sorted(k for k, v in env.items() if SECRET.search(k) and v and not str(v).startswith("op://"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--keep", default="", help="comma-separated core server names")
    ap.add_argument("--keep-file", type=Path, help="file with one core server name per line (# comments ok)")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    cfg = a.config.expanduser()
    if not cfg.exists():
        sys.exit(f"no config at {cfg}")
    keep = {k.strip() for k in a.keep.split(",") if k.strip()}
    if a.keep_file:
        keep |= {ln.split("#")[0].strip() for ln in a.keep_file.read_text().splitlines() if ln.split("#")[0].strip()}
    if not keep:
        sys.exit("give --keep or --keep-file (refusing to park every server)")
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    text = cfg.read_text()

    if cfg.suffix == ".toml":
        pre, servers = toml_blocks(text)
        kept = {n: b for n, b in servers.items() if n in keep}
        parked = {n: b for n, b in servers.items() if n not in keep}
        for n in sorted(servers):
            s = inline_secrets_toml(servers[n]) if n in keep else []
            print(f"  {'keep ' if n in keep else 'park '} {n}" + (f"   ⚠ inline secret {', '.join(s)} → move to 1Password" if s else ""))
        missing = sorted(keep - set(servers))
        if a.apply and parked:
            shutil.copy2(cfg, cfg.with_name(cfg.name + f".bak-{stamp}"))
            pf = cfg.with_name("mcp.parked.toml")
            with open(pf, "a") as f:
                f.write(f"\n# parked {stamp} from {cfg.name}\n" + "".join(parked.values()))
            cfg.write_text(pre.rstrip("\n") + "\n\n" + "".join(kept.values()))
    else:
        data = json.loads(text)
        servers = data.get("mcpServers", {})
        for k in ("apiKey", "api_key", "xaiApiKey"):
            if isinstance(data.get(k), str) and data[k] and not data[k].startswith("op://"):
                print(f"  ⚠ top-level {k} stored in plain text in {cfg.name} → move to 1Password (env var from op)")
        parked = {n: s for n, s in servers.items() if n not in keep}
        for n in sorted(servers):
            s = inline_secrets_json(servers[n]) if n in keep else []
            print(f"  {'keep ' if n in keep else 'park '} {n}" + (f"   ⚠ inline secret {', '.join(s)} → move to 1Password" if s else ""))
        missing = sorted(keep - set(servers))
        if a.apply and parked:
            shutil.copy2(cfg, cfg.with_name(cfg.name + f".bak-{stamp}"))
            pf = cfg.with_name("mcp.parked.json")
            old = json.loads(pf.read_text()) if pf.exists() else {"mcpServers": {}}
            old.setdefault("mcpServers", {}).update(parked)
            pf.write_text(json.dumps(old, indent=2))
            data["mcpServers"] = {n: s for n, s in servers.items() if n in keep}
            cfg.write_text(json.dumps(data, indent=2))
    print(f"\n{len(servers)} servers · keep {len(servers) - len(parked)} · park {len(parked)}"
          + (f" · core servers not configured here: {', '.join(missing)}" if missing else ""))
    print(f"Applied. Backup: {cfg.name}.bak-{stamp}" if a.apply and parked else "Dry run. Re-run with --apply.")


if __name__ == "__main__":
    main()
