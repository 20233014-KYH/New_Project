#!/usr/bin/env python3
"""36개 저장소의 설치 형태를 GitHub API로만(내려받기 없이) 확인한다.
기록: 저장소 크기, 기본 브랜치, 최신 릴리스, plugin.json / marketplace.json / SKILL.md 위치, package.json 이름, README의 설치 줄.
"""
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = json.load(open(os.path.join(HERE, "..", "..", "..", "데이터", "점검_잠정36.json"), encoding="utf-8"))


def gh(path, raw=False):
    args = ["gh", "api", path] + (["-H", "Accept: application/vnd.github.raw"] if raw else [])
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return None
    return r.stdout if raw else json.loads(r.stdout)


out = []
for t in TOOLS:
    rid = t["id"]
    info = gh(f"repos/{rid}") or {}
    full = info.get("full_name", rid)
    br = info.get("default_branch", "main")
    tree = gh(f"repos/{full}/git/trees/{br}?recursive=1") or {}
    paths = [x["path"] for x in tree.get("tree", [])]
    rel = gh(f"repos/{full}/releases/latest") or {}
    pkg = gh(f"repos/{full}/contents/package.json", raw=True)
    pkg_name = None
    if pkg:
        try:
            pkg_name = json.loads(pkg).get("name")
        except Exception:
            pass
    readme = gh(f"repos/{full}/readme", raw=True) or ""
    install = sorted({m.strip()[:160] for m in re.findall(r"^\s*((?:claude (?:mcp add|plugin)|/plugin (?:marketplace add|install)|npx -y [^\n]+|uvx [^\n]+|npm (?:i|install) -g [^\n]+|pip install [^\n]+|brew install [^\n]+|git clone [^\n]+|curl [^\n]+\| *(?:sh|bash)).*)$", readme, re.M)})[:8]
    out.append({
        "id": rid, "full": full, "cat": t["cat"], "size_kb": info.get("size"), "branch": br, "truncated": tree.get("truncated"),
        "release": rel.get("tag_name"), "assets": [(a["name"], a["size"]) for a in rel.get("assets", [])][:12],
        "plugin_json": [p for p in paths if p.endswith(".claude-plugin/plugin.json")][:10],
        "marketplace_json": [p for p in paths if p.endswith(".claude-plugin/marketplace.json")][:3],
        "skill_md": len([p for p in paths if p.endswith("SKILL.md")]), "skill_md_sample": [p for p in paths if p.endswith("SKILL.md")][:5],
        "mcp_json": [p for p in paths if p.endswith(".mcp.json")][:3], "pkg_name": pkg_name, "install_lines": install,
    })
    print(rid, "| size", info.get("size"), "| plugin", len(out[-1]["plugin_json"]), "| mkt", len(out[-1]["marketplace_json"]), "| skills", out[-1]["skill_md"], "| pkg", pkg_name, "| rel", rel.get("tag_name"), flush=True)
json.dump(out, open(os.path.join(HERE, "probe.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
