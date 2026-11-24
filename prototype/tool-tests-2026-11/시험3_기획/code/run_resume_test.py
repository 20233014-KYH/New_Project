#!/usr/bin/env python3
"""시험 3 이어 하기: 세션이 끊겨도 하던 일을 이어 가나 (gsd-core, planning-with-files).

- 과제: 꼬인 할 일 앱(fixture_tangled)에 마감일 기능. 세션 1 = 단계 계획 + 1단계만 구현, 세션 2 = 새 세션에서 "이어서"
- 조건: none(도구 없음) / pwf(planning-with-files, 세션 1에 /planning-with-files:plan) /
        gsd(gsd-core, 세션 1에 /gsd-core:gsd:quick, 세션 2에 /gsd-core:gsd:resume-work)
- 세션 2는 --resume 없이 새로 시작한다(대화 기억 없음, 폴더만 같음)
- 명령 실행은 정해 둔 것만 허용(python·pytest·git·node·ls·cat·mkdir), 인터넷은 막음. 깨끗한 환경은 v3와 같음
- 끝나면 우리가 직접 pytest를 돌려 통과 여부를 기록
사용법: python run_resume_test.py [키 ...]   (없으면 3조건 x 3번)
"""
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import run_plan_test_v3 as v3
from run_plan_test_v4 import plugin_dirs

v1 = v3.v1
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results_resume")
CWDS = os.path.join(HERE, "_cwd_resume")
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
v1.ALLOWED = ("Read,Glob,Grep,Write,Edit,Skill,TodoWrite,Task,"
              "Bash(python:*),Bash(python -m pytest:*),Bash(pytest:*),Bash(git:*),Bash(node:*),Bash(ls:*),Bash(cat:*),Bash(mkdir:*)")
v1.DENIED = "WebFetch,WebSearch"

TASK_A = ("이 할 일 앱에 마감일 기능을 넣을 거야. 전체를 단계로 나눠 계획을 세우고, 오늘은 1단계(저장 형식에 마감일 추가와 "
          "기존 데이터 호환)만 구현하고 테스트까지 통과시켜 줘. 나머지 단계는 다음 세션에서 할 거야.")
TASK_B = "어제 하던 마감일 작업 이어서 해 줘. 남은 단계 중 다음 단계 하나를 진행하고 테스트까지 통과시켜 줘."
CONDITIONS = {
    "none": dict(),
    "pwf": dict(plugins=plugin_dirs("OthmanAdi_planning-with-files"), a="/planning-with-files:plan "),
    "gsd": dict(plugins=plugin_dirs("open-gsd_gsd-core"), a="/gsd-core:gsd:quick ", b="/gsd-core:gsd:resume-work "),
}


def pytest_ok(cwd):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=cwd, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=env, timeout=300)
    return r.returncode == 0, r.stdout[-300:]


def read(cwd, rel):
    p = os.path.join(cwd, rel)
    return open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else ""


def run_one(key):
    cname, rep = key.rsplit("_r", 1)
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    cond = CONDITIONS[cname]
    cwd = os.path.join(CWDS, key)
    shutil.rmtree(cwd, ignore_errors=True)
    shutil.copytree(os.path.join(HERE, "fixture_tangled"), cwd, ignore=shutil.ignore_patterns("__pycache__"))
    g = ["git", "-c", "user.name=test", "-c", "user.email=test@example.com"]
    subprocess.run(["git", "init", "-q"], cwd=cwd)
    subprocess.run(g + ["add", "-A"], cwd=cwd)
    subprocess.run(g + ["commit", "-qm", "start"], cwd=cwd)

    a = v1.run_turn(cwd, cond, cond.get("a", "") + TASK_A, key, 1)
    a_ok, a_log = pytest_ok(cwd)
    code_a = {f: read(cwd, f) for f in ("todo/storage.py", "todo/model.py", "todo/cli.py", "todo/web.py")}
    b = v1.run_turn(cwd, cond, cond.get("b", "") + TASK_B, key, 2)  # 새 세션(--resume 없음)
    b_ok, b_log = pytest_ok(cwd)
    code_b = {f: read(cwd, f) for f in code_a}
    btxt = "\n".join(b["texts"])
    rec = dict(condition=cname, rep=int(rep), turnA=a, turnB=b, a_tests=a_ok, b_tests=b_ok, a_log=a_log, b_log=b_log,
               due_after_a=any("due" in v for v in code_a.values()),
               overdue_after_b=any(k in (code_b["todo/cli.py"] + code_b["todo/web.py"]) for k in ("overdue", "is_overdue", "지난")),
               b_changed_code=code_a != code_b,
               b_knew_done=any(k in btxt for k in ("이미", "완료", "끝났", "구현되어", "되어 있")),
               plan_files=sorted(f for f in os.listdir(cwd) if f.endswith(".md") and f != "README.md") +
                          (["./.planning/"] if os.path.isdir(os.path.join(cwd, ".planning")) else []))
    tk = {}
    for name, t in (("A", a), ("B", b)):
        u = v1.tokens(t["usage"])
        tk[name] = dict(total_in=u["input"] + u["cache_create"] + u["cache_read"], output=u["output"], turns=t["turns"], sec=t["sec"])
    rec["tokens"] = tk
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return (f"{key}: A테스트={a_ok} B테스트={b_ok} B코드변경={rec['b_changed_code']} 지난표시={rec['overdue_after_b']} "
            f"계획파일={rec['plan_files']} B입력={tk['B']['total_in']}")


if __name__ == "__main__":
    keys = sys.argv[1:] or [f"{c}_r{r}" for r in range(1, 4) for c in CONDITIONS]
    with ThreadPoolExecutor(max_workers=3) as ex:
        for msg in ex.map(run_one, keys):
            print(msg, flush=True)
