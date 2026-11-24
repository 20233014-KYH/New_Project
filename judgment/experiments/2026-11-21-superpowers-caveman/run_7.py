"""시험 7: superpowers × caveman 같이 켜기 — 어려운 버그에서도 디버깅 절차를 건너뛰는지, 결과가 같은지.
- 과제: billing 고객 신고 2건(증상은 청구서, 원인은 cycle.py·discount.py 두 군데). 숨은 테스트 12개로 채점.
- 조건: sp(superpowers 7.0.2만) / sp_cav(superpowers 7.0.2 + caveman 4.1.0), 3번씩. 모두 --plugin-dir로 이 실행에만 불러옴(설치 안 함).
- 깨끗한 설정(CLAUDE_CONFIG_DIR=~/.claude-clean), 모델 sonnet. 결과는 실행마다 저장해 끊겨도 이어서.
사용: python run_7.py [reps]
"""
import json, os, re, shutil, subprocess, sys, time

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixture")
HIDDEN = os.path.join(HERE, "hidden", "test_hidden.py")
OUT = os.path.join(HERE, "results")
RUNS = os.path.join(HERE, "_runs")
SP = os.path.join(HERE, "tools", "superpowers")
CAV = os.path.join(HERE, "tools", "caveman")
CLAUDE = os.path.expanduser("~/.local/bin/claude.exe")
CLEAN = os.path.expanduser("~/.claude-clean")
COND = {"sp": [SP], "sp_cav": [SP, CAV]}
PROMPT = """고객 신고 두 건이 들어왔어요.
1) 3월 31일에 가입한 고객의 청구서 기간 끝이 5월 1일로 찍혀요.
2) 103원 상품에 50% 쿠폰 두 장을 쓰면 26원이 청구돼요. 고객은 약관대로면 25원이 맞다고 해요.
README의 약관을 기준으로 원인을 찾아 고쳐 주세요. 기존 테스트는 계속 통과해야 해요."""
os.makedirs(OUT, exist_ok=True)
os.makedirs(RUNS, exist_ok=True)


def run_one(cond, rep):
    name = f"{cond}_r{rep}"
    dst = os.path.join(OUT, name + ".json")
    if os.path.exists(dst):
        return json.load(open(dst, encoding="utf-8"))
    cwd = os.path.join(RUNS, name)
    if os.path.exists(cwd):
        shutil.rmtree(cwd)
    shutil.copytree(FIX, cwd)
    subprocess.run("git init -q && git add -A && git commit -qm start", cwd=cwd, shell=True,
                   env=dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t"))
    cmd = [CLAUDE, "-p", PROMPT, "--setting-sources", "project", "--settings", "{}", "--strict-mcp-config",
           "--no-session-persistence", "--output-format", "stream-json", "--verbose", "--model", "sonnet",
           "--max-turns", "60", "--permission-mode", "bypassPermissions"]
    for p in COND[cond]:
        cmd += ["--plugin-dir", p]
    t0 = time.time()
    r = subprocess.run(cmd, cwd=cwd, env=dict(os.environ, CLAUDE_CONFIG_DIR=CLEAN), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=1800)
    open(os.path.join(OUT, name + ".jsonl"), "w", encoding="utf-8").write(r.stdout)
    skills, usage, plugins, turns = [], {}, None, None
    for line in r.stdout.splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("type") == "system" and e.get("subtype") == "init":
            plugins = [p.get("name") if isinstance(p, dict) else p for p in e.get("plugins", [])]
        elif e.get("type") == "assistant":
            for c in (e.get("message") or {}).get("content", []):
                if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Skill":
                    skills.append((c.get("input") or {}).get("skill") or (c.get("input") or {}).get("command"))
        elif e.get("type") == "result":
            usage, turns = e.get("usage") or {}, e.get("num_turns")
    # 채점: 숨은 테스트 12개 + 기존 테스트 3개(모델이 새로 쓴 테스트는 세지 않음)
    shutil.copy(HIDDEN, os.path.join(cwd, "tests", "test_hidden_grade.py"))
    g = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_hidden_grade.py", "tests/test_basic.py"], cwd=cwd,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    m_pass = re.search(r"(\d+) passed", g.stdout)
    m_fail = re.search(r"(\d+) failed", g.stdout)
    u = {k: usage.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")}
    res = {"cond": cond, "rep": rep, "sec": round(time.time() - t0), "rc": r.returncode, "plugins": plugins, "skills": skills,
           "debug_skill": any(s and "debugging" in s for s in skills), "turns": turns,
           "tests_passed": int(m_pass.group(1)) if m_pass else 0, "tests_failed": int(m_fail.group(1)) if m_fail else 0,
           "usage": u, "total_tokens": sum(u.values()),
           "price_weighted": round(u["input_tokens"] + 1.25 * u["cache_creation_input_tokens"] + 0.1 * u["cache_read_input_tokens"] + 5 * u["output_tokens"]),
           "stderr_tail": r.stderr[-300:]}
    json.dump(res, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return res


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    for rep in range(1, reps + 1):
        for cond in COND:
            x = run_one(cond, rep)
            print(f"{cond}_r{rep}: 테스트 {x['tests_passed']}/15  디버깅 스킬 {'O' if x['debug_skill'] else 'X'} {x['skills']}  "
                  f"토큰 {x['total_tokens']:,} (가중 {x['price_weighted']:,})  {x['sec']}초  플러그인 {x['plugins']}", flush=True)
