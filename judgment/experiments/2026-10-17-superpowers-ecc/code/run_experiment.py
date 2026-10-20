#!/usr/bin/env python3
"""성능·직접 충돌 실험: 과제 3개 x 조합 3개(superpowers / ECC / 둘 다) x 3회 = 27번.

실행마다 새 폴더에 과제 파일을 복사하고 git 저장소로 만든 뒤 Claude Code를 실행한다.
끝나면 그 폴더에서 테스트를 '따로' 다시 돌려 실제로 됐는지 확인한다.
기록: 턴 수, 입력·출력 토큰, 시간, 호출된 스킬·에이전트, 훅 이상(막힘/실패), 권한 거부, 도구 오류,
      검증(테스트 통과, 테스트 파일 손대지 않음, 커밋 여부)
실행 순서는 회차 → 과제 → 조합으로 섞어서 시간대 영향을 줄인다. 이미 결과가 있으면 건너뛴다(이어하기).
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
OUT = os.path.join(HERE, "real_test", "exp")
RUNS = os.path.join(HERE, "_runs")
os.makedirs(OUT, exist_ok=True)
CLAUDE = os.path.expanduser("~/.local/bin/claude.exe")
MODEL = os.environ.get("EXP_MODEL", "sonnet")

PLUGINS = {
    "sp": {"superpowers@superpowers-dev": True},
    "ecc": {"ecc@ecc": True},
    "both": {"superpowers@superpowers-dev": True, "ecc@ecc": True},
}
TASKS = {
    "tdd": ("tdd", "Create a Python function slugify(text) in slugify.py that turns a title into a URL slug (lowercase, spaces to hyphens, drop punctuation). Add unit tests in test_slugify.py and make them pass. Use test-driven development.", ["test_slugify.py"]),
    "bugfix": ("bugfix", "The tests in test_calc.py are failing. Find and fix the bugs in calc.py so all tests pass. Do not modify test_calc.py.", ["test_calc.py"]),
    "refactor": ("refactor", "Refactor report.py to remove the duplicated code without changing its behavior. Keep test_report.py passing and do not edit it. When you are done, commit your change with git.", ["test_report.py"]),
}


def sh(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None


def prepare(task, run_dir):
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir, ignore_errors=True)
    os.makedirs(run_dir)
    src = os.path.join(FIX, TASKS[task][0])
    for f in os.listdir(src):
        if f.endswith(".py"):
            shutil.copy(os.path.join(src, f), run_dir)
    sh(["git", "init", "-q"], run_dir)
    sh(["git", "config", "user.name", "pilot"], run_dir)
    sh(["git", "config", "user.email", "pilot@example.com"], run_dir)
    sh(["git", "add", "-A"], run_dir)
    sh(["git", "commit", "-q", "-m", "initial", "--allow-empty"], run_dir)


def analyze(stdout):
    init = result = None
    skills, agents, tool_errors, hooks_bad, hook_block_text, tools = [], [], 0, [], [], {}
    for line in stdout.splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        t, st = e.get("type"), e.get("subtype")
        if t == "system" and st == "init":
            init = e
        elif t == "result":
            result = e
        elif t == "assistant":
            for c in (e.get("message") or {}).get("content", []):
                if c.get("type") == "tool_use":
                    tools[c["name"]] = tools.get(c["name"], 0) + 1
                    if c["name"] == "Skill":
                        skills.append((c.get("input") or {}).get("skill"))
                    if c["name"] in ("Task", "Agent"):
                        agents.append((c.get("input") or {}).get("subagent_type"))
        elif t == "user":
            for c in (e.get("message") or {}).get("content", []) if isinstance((e.get("message") or {}).get("content"), list) else []:
                if c.get("type") == "tool_result" and c.get("is_error"):
                    tool_errors += 1
        elif t == "system" and st == "hook_response":
            out = (e.get("stdout") or "") + (e.get("stderr") or "")
            if e.get("outcome") not in ("success", None) or str(e.get("exit_code")) not in ("0", "None"):
                hooks_bad.append({"hook": e.get("hook_name"), "outcome": e.get("outcome"), "exit": e.get("exit_code"), "text": out[:300]})
            low = out.lower()
            if any(k in low for k in ('"decision":"block"', '"decision": "block"', "permissiondecision", "blocked", "denied")):
                hook_block_text.append({"hook": e.get("hook_name"), "text": out[:300]})
    return init, result, skills, agents, tool_errors, hooks_bad, hook_block_text, tools


def run_one(rep, task, combo):
    name = f"r{rep}_{task}_{combo}"
    summ_path = os.path.join(OUT, name + ".json")
    if os.path.exists(summ_path):
        return json.load(open(summ_path, encoding="utf-8"))
    run_dir = os.path.join(RUNS, name)
    prepare(task, run_dir)
    test_files = TASKS[task][2]
    before = {f: sha(os.path.join(run_dir, f)) for f in test_files}
    settings = json.dumps({"enabledPlugins": PLUGINS[combo]})
    cmd = [CLAUDE, "-p", TASKS[task][1], "--setting-sources", "project", "--settings", settings, "--strict-mcp-config",
           "--no-session-persistence", "--output-format", "stream-json", "--verbose", "--include-hook-events",
           "--model", MODEL, "--max-turns", "30", "--permission-mode", "bypassPermissions"]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=run_dir, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1200)
        stdout, rc, timed_out = r.stdout, r.returncode, False
    except subprocess.TimeoutExpired as ex:
        stdout, rc, timed_out = (ex.stdout or ""), -1, True
    wall = round(time.time() - t0, 1)
    open(os.path.join(OUT, name + ".jsonl"), "w", encoding="utf-8").write(stdout if isinstance(stdout, str) else stdout.decode("utf-8", "replace"))
    init, result, skills, agents, tool_errors, hooks_bad, hook_block, tools = analyze(stdout if isinstance(stdout, str) else "")
    # 독립 검증
    py = sh([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], run_dir)
    last = (py.stdout.strip().splitlines() or [""])[-1]
    tests_exist = all(os.path.exists(os.path.join(run_dir, f)) for f in test_files)
    tests_untouched = all(before[f] == sha(os.path.join(run_dir, f)) for f in test_files) if task != "tdd" else None
    commits = int((sh(["git", "rev-list", "--count", "HEAD"], run_dir).stdout or "0").strip() or 0)
    u = (result or {}).get("usage", {})
    summ = {
        "name": name, "rep": rep, "task": task, "combo": combo, "model": MODEL, "returncode": rc, "timed_out": timed_out, "wall_s": wall,
        "num_turns": (result or {}).get("num_turns"), "is_error": (result or {}).get("is_error"),
        "input_sum": sum((u.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")),
        "output_tokens": u.get("output_tokens"), "cost_usd_equiv": (result or {}).get("total_cost_usd"),
        "skills": skills, "agents": agents, "tools": tools, "tool_errors": tool_errors,
        "hooks_bad": hooks_bad, "hook_block_text": hook_block, "permission_denials": (result or {}).get("permission_denials"),
        "verify": {"pytest": last, "passed": (" passed" in last and "failed" not in last and "error" not in last), "tests_exist": tests_exist,
                   "tests_untouched": tests_untouched, "commits": commits, "committed": commits > 1},
        "result_text": ((result or {}).get("result") or "")[:400],
    }
    json.dump(summ, open(summ_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return summ


def main():
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    for rep in range(1, reps + 1):
        for task in TASKS:
            for combo in PLUGINS:
                s = run_one(rep, task, combo)
                v = s["verify"]
                print(f"{s['name']:<22} 턴 {s['num_turns']} 입력 {s['input_sum']:,} 출력 {s['output_tokens']} {s['wall_s']}s | 통과 {v['passed']} 커밋 {v['committed']} 테스트보존 {v['tests_untouched']} | 스킬 {s['skills']} 에이전트 {s['agents']} | 훅이상 {len(s['hooks_bad'])} 막힘흔적 {len(s['hook_block_text'])} 권한거부 {len(s['permission_denials'] or [])}", flush=True)


if __name__ == "__main__":
    main()
