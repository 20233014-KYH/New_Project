#!/usr/bin/env python3
"""36개 도구를 하나씩만 켜고 '처음 읽는 양(첫 응답 입력 토큰)'을 2번씩 잰다.

- 플러그인: 저장소의 marketplace.json 에 있는 플러그인 전부를 --plugin-dir 로 이 세션에만 불러온다(전체 설치 기준).
- MCP 서버: --mcp-config 로 이 세션에만 연결한다. 키가 필요한 서버는 가짜 값(dummy-not-real)을 넣는다.
- 스킬·명령 파일: 측정 폴더의 .claude/ 안에 둔다(프로젝트 범위). 사용자 설정은 건드리지 않는다.
- 결과: results/<id>_<회차>.json, results/<id>_<회차>.jsonl
사용법: python measure36.py [도구id ...]   (없으면 전부, 이미 잰 것은 건너뜀)
"""
import json
import re
import os
import shutil
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "repos")
SB = os.path.join(HERE, "..", "tools_sandbox")
NPMBIN = os.path.join(HERE, "npm", "node_modules", ".bin")
OUT = os.path.join(HERE, "results")
CWDS = os.path.join(HERE, "_cwd")
os.makedirs(OUT, exist_ok=True)
CLAUDE = os.path.expanduser("~/.local/bin/claude.exe")
IMPECCABLE = os.path.expanduser("~/.claude/plugins/cache/impeccable/impeccable/4.0.4")
FAKE = "dummy-not-real"


def mkt(repo):
    """marketplace.json 에 적힌 플러그인 폴더 전부."""
    root = os.path.join(R, repo)
    d = json.load(open(os.path.join(root, ".claude-plugin", "marketplace.json"), encoding="utf-8"))
    dirs = []
    for p in d.get("plugins", []):
        src = p.get("source")
        if isinstance(src, str):
            dirs.append(os.path.normpath(os.path.join(root, src)))
    return dirs


NODE_MODULES = os.path.join(HERE, "npm", "node_modules")
PKG_OF_BIN = {}
for _root, _dirs, _files in os.walk(NODE_MODULES):
    if "package.json" in _files and os.path.basename(os.path.dirname(_root)) in ("node_modules",) or (os.path.basename(os.path.dirname(os.path.dirname(_root))) == "node_modules" and os.path.basename(os.path.dirname(_root)).startswith("@")):
        try:
            _j = json.load(open(os.path.join(_root, "package.json"), encoding="utf-8"))
        except Exception:
            _dirs[:] = []
            continue
        _b = _j.get("bin")
        if isinstance(_b, str):
            _b = {_j.get("name", "").split("/")[-1]: _b}
        for _n, _f in (_b or {}).items():
            PKG_OF_BIN.setdefault(_n, os.path.normpath(os.path.join(_root, _f)))
        PKG_OF_BIN.setdefault("pkg:" + _j.get("name", ""), os.path.normpath(os.path.join(_root, list((_b or {"x": ""}).values())[0])) if _b else None)
        _dirs[:] = [d for d in _dirs if d == "node_modules"]


def bin_(name):
    """Windows .cmd 를 거치면 연결이 늦어지는 서버가 있어, node 로 바로 실행한다."""
    return ("node", PKG_OF_BIN[name])


def stdio(cmd, args, env=None):
    if isinstance(cmd, tuple):
        cmd, args = cmd[0], [cmd[1]] + list(args)
    s = {"type": "stdio", "command": cmd, "args": args}
    if env:
        s["env"] = env
    return s


def setup_gstack(cwd):
    # gstack setup 은 저장소의 스킬 폴더를 ~/.claude/skills/<이름> 으로 하나씩 등록한다. 같은 모양을 프로젝트 범위로 만든다.
    root = os.path.join(R, "garrytan_gstack")
    dst = os.path.join(cwd, ".claude", "skills")
    os.makedirs(dst, exist_ok=True)
    shutil.copytree(root, os.path.join(dst, "gstack"), ignore=shutil.ignore_patterns(".git", "node_modules"), dirs_exist_ok=True)
    for n in os.listdir(root):
        if os.path.isfile(os.path.join(root, n, "SKILL.md")):
            os.makedirs(os.path.join(dst, n), exist_ok=True)
            shutil.copy(os.path.join(root, n, "SKILL.md"), os.path.join(dst, n, "SKILL.md"))


def setup_secreview(cwd):
    d = os.path.join(cwd, ".claude", "commands")
    os.makedirs(d, exist_ok=True)
    shutil.copy(os.path.join(R, "anthropics_claude-code-security-review", ".claude", "commands", "security-review.md"), d)


def setup_graphify(cwd):
    exe = os.path.join(HERE, "venv_graphify", "Scripts", "graphify.exe")
    r = subprocess.run([exe, "install", "--project", "--platform", "claude"], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    open(os.path.join(cwd, "_graphify_install.txt"), "w", encoding="utf-8").write(r.stdout + r.stderr)


# id: dict(plugins=[...], mcp={...}, setup=fn, path=[...], note="")
TOOLS = {
    "_none": dict(note="도구 없음(기준값, 처음)"),
    "obra/superpowers": dict(plugins=mkt("obra_superpowers")),
    "affaan-m/ECC": dict(plugins=mkt("affaan-m_ECC")),
    "garrytan/gstack": dict(setup=setup_gstack, note="setup 스크립트가 하는 스킬 등록을 프로젝트 범위로 재현(브라우저 바이너리 빌드는 안 함)"),
    "open-gsd/gsd-core": dict(plugins=mkt("open-gsd_gsd-core")),
    "OthmanAdi/planning-with-files": dict(plugins=mkt("OthmanAdi_planning-with-files")),
    "phuryn/pm-skills": dict(plugins=mkt("phuryn_pm-skills")),
    "JuliusBrussee/caveman": dict(plugins=[os.path.join(SB, "caveman")]),
    "rtk-ai/rtk": dict(hooks={"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": 'bash "' + os.path.join(SB, "hooks", "rtk-rewrite.sh").replace("\\", "/") + '"'}]}]},
                       path=[os.path.join(SB, "bin")]),
    "headroomlabs-ai/headroom": dict(plugins=mkt("headroomlabs-ai_headroom"), path=[os.path.join(HERE, "venv_headroom", "Scripts")],
                                     note="주 기능은 프록시(세션 밖). 여기서는 플러그인 2개만 잼"),
    "thedotmack/claude-mem": dict(plugins=mkt("thedotmack_claude-mem")),
    "jarrodwatts/claude-hud": dict(plugins=[os.path.join(SB, "claude-hud")]),
    "ccusage/ccusage": dict(skip="명령줄 도구. 세션에 읽히는 것 없음(README 기준)"),
    "Graphify-Labs/graphify": dict(setup=setup_graphify, path=[os.path.join(HERE, "venv_graphify", "Scripts")], note="graphify install --project 결과로 잼"),
    "colbymchenry/codegraph": dict(mcp={"codegraph": stdio(bin_("codegraph"), ["serve", "--mcp"])}),
    "zilliztech/claude-context": dict(mcp={"claude-context": stdio(bin_("claude-context-mcp"), [], {"OPENAI_API_KEY": FAKE, "MILVUS_ADDRESS": "localhost:19530"})},
                                      note="키 가짜 값"),
    "upstash/context7": dict(plugins=mkt("upstash_context7")),
    "oraios/serena": dict(mcp={"serena": stdio(os.path.join(HERE, "venv_serena", "Scripts", "serena.exe"),
                                               ["start-mcp-server", "--context", "claude-code", "--project-from-cwd",
                                                "--enable-web-dashboard", "false", "--open-web-dashboard", "false"])}),
    "Egonex-AI/Understand-Anything": dict(plugins=mkt("Egonex-AI_Understand-Anything")),
    "nextlevelbuilder/ui-ux-pro-max-skill": dict(plugins=mkt("nextlevelbuilder_ui-ux-pro-max-skill")),
    "Leonxlnx/taste-skill": dict(plugins=mkt("Leonxlnx_taste-skill")),
    "pbakaus/impeccable": dict(plugins=[IMPECCABLE], note="이 컴퓨터에 설치된 4.0.4"),
    "GLips/Figma-Context-MCP": dict(mcp={"figma": stdio(bin_("figma-developer-mcp"), ["--figma-api-key=" + FAKE, "--stdio"])}, note="키 가짜 값"),
    "grab/cursor-talk-to-figma-mcp": dict(mcp={"TalkToFigma": stdio(bin_("cursor-talk-to-figma-mcp"), [])}, note="bun 대신 node로 실행"),
    "Jpisnice/shadcn-ui-mcp-server": dict(mcp={"shadcn": stdio(bin_("shadcn-mcp"), [])}),
    "bytebase/dbhub": dict(plugins=mkt("bytebase_dbhub"), note="DSN 없음"),
    "googleapis/mcp-toolbox": dict(skip="Windows 실행 파일 294MB + 실제 DB 필요 → 실측 안 함"),
    "supabase/mcp": dict(mcp={"supabase": stdio(bin_("mcp-server-supabase"), ["--read-only"], {"SUPABASE_ACCESS_TOKEN": FAKE})}, note="토큰 가짜 값"),
    "containers/kubernetes-mcp-server": dict(mcp={"kubernetes": stdio(bin_("kubernetes-mcp-server"), [])}, note="kubeconfig 없음"),
    "Flux159/mcp-server-kubernetes": dict(mcp={"kubernetes": stdio(bin_("mcp-server-kubernetes"), [])}, note="kubeconfig 없음"),
    "hashicorp/terraform-mcp-server": dict(mcp={"terraform": stdio(os.path.join(HERE, "bin", "terraform-mcp-server.exe"), ["stdio"])}),
    "microsoft/playwright-mcp": dict(mcp={"playwright": stdio(bin_("playwright-mcp"), [])}),
    "ChromeDevTools/chrome-devtools-mcp": dict(plugins=mkt("ChromeDevTools_chrome-devtools-mcp")),
    "alibaba/open-code-review": dict(plugins=mkt("alibaba_open-code-review")),
    "nizos/tdd-guard": dict(plugins=mkt("nizos_tdd-guard"), path=[NPMBIN]),
    "trailofbits/skills": dict(plugins=mkt("trailofbits_skills")),
    "anthropics/claude-code-security-review": dict(setup=setup_secreview, note="주 기능은 GitHub Action. 여기서는 명령 파일만 잼"),
    "_none_end": dict(note="도구 없음(기준값, 끝)"),
}


def plugin_mcp(d):
    """--strict-mcp-config 에서는 플러그인 안의 MCP 서버가 안 붙는다. 플러그인의 .mcp.json / plugin.json 의 mcpServers 를 직접 읽어 넘긴다."""
    found = {}
    pj = os.path.join(d, ".claude-plugin", "plugin.json")
    srcs = []
    if os.path.exists(os.path.join(d, ".mcp.json")):
        srcs.append(json.load(open(os.path.join(d, ".mcp.json"), encoding="utf-8")).get("mcpServers", {}))
    if os.path.exists(pj):
        v = json.load(open(pj, encoding="utf-8")).get("mcpServers")
        if isinstance(v, str) and os.path.exists(os.path.join(d, v)):
            srcs.append(json.load(open(os.path.join(d, v), encoding="utf-8")).get("mcpServers", {}))
        elif isinstance(v, dict):
            srcs.append(v)
    for s in srcs:
        found.update(s)
    for k, v in found.items():  # npx 패키지가 이 폴더에 설치돼 있으면 node 로 바로 실행
        if v.get("command") == "npx":
            args = list(v.get("args", []))
            pkg = next((a for a in args if not a.startswith("-")), "")
            name = pkg.rsplit("@", 1)[0] if pkg.count("@") > (1 if pkg.startswith("@") else 0) else pkg
            js = PKG_OF_BIN.get("pkg:" + name)
            if js:
                rest = args[args.index(pkg) + 1:]
                found[k] = dict(v, command="node", args=[js] + rest)
    txt = json.dumps(found).replace("${CLAUDE_PLUGIN_ROOT}", d.replace("\\", "/"))
    txt = re.sub(r"\$\{user_config\.[^}]*\}", "", txt)
    return json.loads(txt)


def safe(i):
    return i.replace("/", "__")


def run(tid, rep):
    t = TOOLS[tid]
    name = f"{safe(tid)}_{rep}"
    p = os.path.join(OUT, name + ".json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    cwd = os.path.join(CWDS, safe(tid))
    if rep == 1 and os.path.exists(cwd):
        shutil.rmtree(cwd, ignore_errors=True)
    os.makedirs(cwd, exist_ok=True)
    if rep == 1 and t.get("setup"):
        t["setup"](cwd)
    settings = {"enabledPlugins": {}}
    if t.get("hooks"):
        settings["hooks"] = t["hooks"]
    cmd = [CLAUDE, "-p", "Reply with exactly one word: ok", "--setting-sources", "project", "--settings", json.dumps(settings),
           "--strict-mcp-config", "--no-session-persistence", "--output-format", "stream-json", "--verbose", "--include-hook-events",
           "--model", "haiku", "--max-turns", "1", "--permission-mode", "bypassPermissions"]
    for d in t.get("plugins", []):
        cmd += ["--plugin-dir", d]
    mcp = dict(t.get("mcp", {}))
    for d in t.get("plugins", []):
        mcp.update(plugin_mcp(d))
    if mcp:
        cmd += ["--mcp-config", json.dumps({"mcpServers": mcp})]
    env = dict(os.environ, MCP_CONNECTION_NONBLOCKING="0", DO_NOT_TRACK="1", FRAMELINK_TELEMETRY="off")  # "0" = MCP 서버가 연결될 때까지 기다린 뒤 시작, 텔레메트리 끔
    if t.get("path"):
        env["PATH"] = os.pathsep.join(t["path"]) + os.pathsep + env["PATH"]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        stdout, rc = r.stdout, r.returncode
    except subprocess.TimeoutExpired as ex:
        stdout, rc = ex.stdout or "", -1
        stdout = stdout if isinstance(stdout, str) else stdout.decode("utf-8", "replace")
    open(os.path.join(OUT, name + ".jsonl"), "w", encoding="utf-8").write(stdout)
    init = result = None
    hooks, hook_bad = {}, []
    for line in stdout.splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("type") == "system" and e.get("subtype") == "init":
            init = e
        elif e.get("type") == "result":
            result = e
        elif e.get("type") == "system" and e.get("subtype") == "hook_response":
            n = e.get("hook_name") or "?"
            hooks[n] = hooks.get(n, 0) + 1
            if e.get("outcome") not in ("success", None) or str(e.get("exit_code")) not in ("0", "None"):
                hook_bad.append({"hook": n, "exit": e.get("exit_code"), "text": ((e.get("stderr") or "") + (e.get("output") or ""))[:200]})
    if "hit your" in ((result or {}).get("result") or ""):
        sys.exit(f"사용 한도에 걸려 멈춤: {name}")
    u = (result or {}).get("usage", {})
    tools = (init or {}).get("tools", [])
    s = {"id": tid, "rep": rep, "rc": rc, "wall_s": round(time.time() - t0, 1),
         "context_in_tokens": sum((u.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")),
         "plugins": [x.get("name") if isinstance(x, dict) else x for x in (init or {}).get("plugins", [])],
         "skills_count": len((init or {}).get("skills", [])), "skills": (init or {}).get("skills", []),
         "slash_commands_count": len((init or {}).get("slash_commands", [])), "agents_count": len((init or {}).get("agents", [])),
         "tools_count": len(tools), "mcp_tools": [x for x in tools if str(x).startswith("mcp__")],
         "mcp_servers": (init or {}).get("mcp_servers"), "hooks_fired": hooks, "hooks_bad": hook_bad,
         "result_text": ((result or {}).get("result") or "")[:120], "note": t.get("note", "")}
    json.dump(s, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return s


def main():
    ids = sys.argv[1:] or list(TOOLS)
    for tid in ids:
        if TOOLS[tid].get("skip"):
            print(f"{tid:<42} 건너뜀: {TOOLS[tid]['skip']}", flush=True)
            continue
        a, b = run(tid, 1), run(tid, 2)
        ms = [(m.get("name"), m.get("status")) for m in (b.get("mcp_servers") or [])]
        print(f"{tid:<42} {a['context_in_tokens']:>7,} / {b['context_in_tokens']:>7,} | 플러그인 {len(b['plugins'])} 스킬 {b['skills_count']} 명령 {b['slash_commands_count']} "
              f"MCP도구 {len(b['mcp_tools'])} 서버 {ms} 훅이상 {len(a['hooks_bad']) + len(b['hooks_bad'])}", flush=True)


if __name__ == "__main__":
    main()
