#!/usr/bin/env python3
"""토큰 절약 도구 실험: caveman(말 줄이기) x rtk(명령 출력 줄이기).

1) ctx  : 첫 응답에서 읽는 양(토큰)을 조건별로 2번씩 잰다. "따로 잰 증가분의 합 ≈ 같이 켠 값"인지 확인.
2) task : 지금 쓰는 조합(superpowers+karpathy+impeccable)을 기준으로 +caveman / +rtk / +둘 다,
          과제 3개 x 3회 = 36번. 끝나면 테스트를 따로 다시 돌려 확인한다.

- caveman 은 --plugin-dir 로 이 세션에만 불러온다(설치 안 함).
- rtk 는 --settings 의 PreToolUse(Bash) 훅으로만 건다(rtk init -g 안 씀). rtk·jq 는 tools_sandbox/bin 에만 있다.
사용법: python run_tools_exp.py ctx | task [회차]
"""
import json
import os
import sys
import time

import run_experiment as base

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
SB = os.path.join(HERE, "tools_sandbox")
OUT = os.path.join(HERE, "real_test", "tools_exp")
RUNS = os.path.join(HERE, "_runs_tools")
os.makedirs(OUT, exist_ok=True)
CAVEMAN = os.path.join(SB, "caveman")
RTK_HOOK = os.path.join(SB, "hooks", "rtk-rewrite.sh").replace("\\", "/")
ENV = dict(os.environ, PATH=os.path.join(SB, "bin") + os.pathsep + os.environ["PATH"])

MINE = {"superpowers@superpowers-dev": True, "andrej-karpathy-skills@karpathy-skills": True, "impeccable@impeccable": True}
RTK_HOOKS = {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": f'bash "{RTK_HOOK}"'}]}]}

# 이름: (내 플러그인 켬?, caveman?, rtk?)
CTX = {"none": (False, False, False), "cav": (False, True, False), "rtk": (False, False, True), "cavrtk": (False, True, True),
       "mine": (True, False, False), "mine_cav": (True, True, False), "mine_rtk": (True, False, True), "mine_both": (True, True, True)}
TASK_COMBOS = ["mine", "mine_cav", "mine_rtk", "mine_both"]


def cmd_for(combo, prompt, model, turns):
    mine, cav, rtk = CTX[combo]
    settings = {"enabledPlugins": MINE if mine else {}}
    if rtk:
        settings["hooks"] = RTK_HOOKS
    c = [base.CLAUDE, "-p", prompt, "--setting-sources", "project", "--settings", json.dumps(settings), "--strict-mcp-config",
         "--no-session-persistence", "--output-format", "stream-json", "--verbose", "--include-hook-events",
         "--model", model, "--max-turns", str(turns), "--permission-mode", "bypassPermissions"]
    if cav:
        c += ["--plugin-dir", CAVEMAN]
    return c


def extra(stdout):
    """rtk 가 실제로 명령을 바꿨는지, 어떤 셸 도구를 썼는지, caveman 훅이 돌았는지."""
    rewrites, hook_names, bash_cmds, nudge = 0, {}, [], False
    for line in stdout.splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("type") == "system" and e.get("subtype") == "hook_response":
            out = (e.get("stdout") or "") + (e.get("output") or "")
            n = e.get("hook_name") or "?"
            hook_names[n] = hook_names.get(n, 0) + 1
            if "updatedInput" in out:
                rewrites += 1
            if "STATUSLINE SETUP NEEDED" in out:
                nudge = True
        elif e.get("type") == "assistant":
            for c in (e.get("message") or {}).get("content", []):
                if c.get("type") == "tool_use" and c.get("name") == "Bash":
                    bash_cmds.append(((c.get("input") or {}).get("command") or "")[:120])
    return {"rtk_rewrites": rewrites, "hooks_fired": hook_names, "bash_cmds": bash_cmds, "caveman_nudge": nudge}


def run(name, combo, prompt, model, turns, cwd):
    import subprocess
    t0 = time.time()
    try:
        r = subprocess.run(cmd_for(combo, prompt, model, turns), cwd=cwd, env=ENV, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=1200)
        stdout, rc, to = r.stdout, r.returncode, False
    except subprocess.TimeoutExpired as ex:
        stdout, rc, to = (ex.stdout or ""), -1, True
        stdout = stdout if isinstance(stdout, str) else stdout.decode("utf-8", "replace")
    wall = round(time.time() - t0, 1)
    open(os.path.join(OUT, name + ".jsonl"), "w", encoding="utf-8").write(stdout)
    return stdout, rc, to, wall


def do_ctx():
    cwd = os.path.join(RUNS, "_ctx")
    os.makedirs(cwd, exist_ok=True)
    for rep in (1, 2):
        for combo in CTX:
            name = f"ctx{rep}_{combo}"
            p = os.path.join(OUT, name + ".json")
            if os.path.exists(p):
                continue
            stdout, rc, to, wall = run(name, combo, "Reply with exactly one word: ok", "haiku", 1, cwd)
            init, result, *_ = base.analyze(stdout)
            u = (result or {}).get("usage", {})
            s = {"name": name, "combo": combo, "rc": rc, "wall_s": wall,
                 "plugins": [x.get("name") if isinstance(x, dict) else x for x in (init or {}).get("plugins", [])],
                 "skills_count": len((init or {}).get("skills", [])),
                 "context_in_tokens": sum((u.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")),
                 "output_tokens": u.get("output_tokens"), "result_text": ((result or {}).get("result") or "")[:200], **extra(stdout)}
            json.dump(s, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"{name:<18} 첫입력 {s['context_in_tokens']:,} 스킬 {s['skills_count']} 넛지 {s['caveman_nudge']} 훅 {s['hooks_fired']}", flush=True)


def do_task(reps):
    base.RUNS = RUNS
    for rep in range(1, reps + 1):
        for task in base.TASKS:
            for combo in TASK_COMBOS:
                name = f"r{rep}_{task}_{combo}"
                p = os.path.join(OUT, name + ".json")
                if os.path.exists(p):
                    continue
                run_dir = os.path.join(RUNS, name)
                base.prepare(task, run_dir)
                tf = base.TASKS[task][2]
                before = {f: base.sha(os.path.join(run_dir, f)) for f in tf}
                stdout, rc, to, wall = run(name, combo, base.TASKS[task][1], "sonnet", 30, run_dir)
                init, result, skills, agents, terr, hbad, hblock, tools = base.analyze(stdout)
                if "hit your" in ((result or {}).get("result") or ""):
                    sys.exit(f"사용 한도에 걸려 멈춤: {name} ({(result or {}).get('result')})")
                py =base.sh([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], run_dir)
                last = (py.stdout.strip().splitlines() or [""])[-1]
                commits = int((base.sh(["git", "rev-list", "--count", "HEAD"], run_dir).stdout or "0").strip() or 0)
                u = (result or {}).get("usage", {})
                s = {"name": name, "rep": rep, "task": task, "combo": combo, "rc": rc, "timed_out": to, "wall_s": wall,
                     "num_turns": (result or {}).get("num_turns"), "is_error": (result or {}).get("is_error"),
                     "input_sum": sum((u.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")),
                     "output_tokens": u.get("output_tokens"), "skills": skills, "agents": agents, "tools": tools, "tool_errors": terr,
                     "hooks_bad": hbad, "permission_denials": (result or {}).get("permission_denials"),
                     "verify": {"pytest": last, "passed": (" passed" in last and "failed" not in last and "error" not in last),
                                "tests_untouched": all(before[f] == base.sha(os.path.join(run_dir, f)) for f in tf) if task != "tdd" else None,
                                "committed": commits > 1},
                     "result_chars": len((result or {}).get("result") or ""), "result_text": ((result or {}).get("result") or "")[:400],
                     **extra(stdout)}
                json.dump(s, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                v = s["verify"]
                print(f"{name:<24} 턴 {s['num_turns']} 입력 {s['input_sum']:,} 출력 {s['output_tokens']} {wall}s | 통과 {v['passed']} 보존 {v['tests_untouched']} 커밋 {v['committed']} | "
                      f"도구 {tools} rtk바꿈 {s['rtk_rewrites']} 훅이상 {len(hbad)} 답글자 {s['result_chars']}", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "ctx":
        do_ctx()
    else:
        do_task(int(sys.argv[2]) if len(sys.argv) > 2 else 3)
