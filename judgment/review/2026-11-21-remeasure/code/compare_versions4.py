"""10/18 measure36.py와 같은 방법으로 최신판 4개 도구의 '처음 읽는 양'과 스킬·명령·훅 수를 다시 잰다.
- 같은 질문("Reply with exactly one word: ok"), haiku, 2번씩, 도구 없음 기준값은 처음·끝에 2번씩.
- 플러그인은 marketplace.json의 플러그인 전부를 --plugin-dir로 이 세션에만 불러옴(설치 안 함).
사용: python remeasure.py
"""
import json, os, shutil, subprocess, sys, time

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "repos")
OUT = os.path.join(HERE, "results")
CWDS = os.path.join(HERE, "_cwd")
os.makedirs(OUT, exist_ok=True)
CLAUDE = os.path.expanduser("~/.local/bin/claude.exe")


def mkt(repo):
    root = os.path.join(R, repo)
    d = json.load(open(os.path.join(root, ".claude-plugin", "marketplace.json"), encoding="utf-8"))
    return [os.path.normpath(os.path.join(root, p["source"])) for p in d.get("plugins", []) if isinstance(p.get("source"), str)]


TOOLS = {
    "_none": [],
    "superpowers": mkt("obra_superpowers"),
    "caveman": mkt("JuliusBrussee_caveman"),
    "pm-skills": mkt("phuryn_pm-skills"),
    "planning-with-files": mkt("OthmanAdi_planning-with-files"),
    # 대조군: 10/18에 잰 옛 버전을 지금 Claude Code로 다시 잼(차이가 도구 탓인지 Claude Code 탓인지 가르기)
    "old_superpowers": mkt("old_obra_superpowers"),
    "old_caveman": mkt("old_JuliusBrussee_caveman"),
    "old_pm-skills": mkt("old_phuryn_pm-skills"),
    "old_planning-with-files": mkt("old_OthmanAdi_planning-with-files"),
    "_none_end": [],
}


def run(tid, rep):
    p = os.path.join(OUT, f"{tid}_{rep}.json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    cwd = os.path.join(CWDS, tid)
    os.makedirs(cwd, exist_ok=True)
    cmd = [CLAUDE, "-p", "Reply with exactly one word: ok", "--setting-sources", "project", "--settings", json.dumps({"enabledPlugins": {}}),
           "--strict-mcp-config", "--no-session-persistence", "--output-format", "stream-json", "--verbose", "--include-hook-events",
           "--model", "haiku", "--max-turns", "1", "--permission-mode", "bypassPermissions"]
    for d in TOOLS[tid]:
        cmd += ["--plugin-dir", d]
    env = dict(os.environ, DO_NOT_TRACK="1")
    t0 = time.time()
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    open(os.path.join(OUT, f"{tid}_{rep}.jsonl"), "w", encoding="utf-8").write(r.stdout)
    init = result = None
    hooks = {}
    for line in r.stdout.splitlines():
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
    if "hit your" in ((result or {}).get("result") or ""):
        sys.exit(f"사용 한도에 걸려 멈춤: {tid}_{rep}")
    u = (result or {}).get("usage", {})
    s = {"id": tid, "rep": rep, "rc": r.returncode, "wall_s": round(time.time() - t0, 1),
         "claude_version": (init or {}).get("claude_code_version"),
         "context_in_tokens": sum((u.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")),
         "plugins": [x.get("name") if isinstance(x, dict) else x for x in (init or {}).get("plugins", [])],
         "skills_count": len((init or {}).get("skills", [])), "slash_commands_count": len((init or {}).get("slash_commands", [])),
         "agents_count": len((init or {}).get("agents", [])), "hooks_fired": hooks,
         "result_text": ((result or {}).get("result") or "")[:80]}
    json.dump(s, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return s


if __name__ == "__main__":
    for tid in TOOLS:
        a, b = run(tid, 1), run(tid, 2)
        print(f"{tid:<22} {a['context_in_tokens']:>7,} / {b['context_in_tokens']:>7,} | 플러그인 {len(b['plugins'])} 스킬 {b['skills_count']} "
              f"명령 {b['slash_commands_count']} 에이전트 {b['agents_count']} 훅 {b['hooks_fired']} | {b['claude_version']} | {b['result_text']!r}", flush=True)
