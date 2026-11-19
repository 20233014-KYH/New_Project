#!/usr/bin/env python3
"""시험 3 다시(v2): 깨끗한 환경에서 상황 4개 x 조건 5개 x 3번.

v1과 달라진 점
- 깨끗한 환경: 시험용 설정 폴더(CLAUDE_CONFIG_DIR=~/.claude-clean)로 실행하고, 시험 PC의 전역 지침
  (~/.claude/CLAUDE.md)은 이 실행에서만 claudeMdExcludes 설정으로 뺀다. 사용자 파일은 건드리지 않는다.
- 조건 추가: gstack_cmd = gstack 명령을 직접 부름(새 아이디어·큰 프로젝트 /office-hours, 코드 수정 /plan-eng-review)
- 같은 조건을 3번씩 돌린다(결과: results_v2/<상황>_<조건>_r<회차>.json)
- 모든 실행에 답변지를 두 번째 대답으로 똑같이 보낸다(조건마다 대화 횟수를 맞춤)
사용법: python run_plan_test_v2.py [키 ...]   (없으면 전부, 이미 한 것은 건너뜀)
"""
import json
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor

import run_plan_test as v1

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results_v2")
CWDS = os.path.join(HERE, "_cwd_v2")
CLEAN_CONFIG = os.path.expanduser("~/.claude-clean")
SETTINGS = json.dumps({"claudeMdExcludes": ["**/.claude/CLAUDE.md", "C:/Users/User/.claude/CLAUDE.md"]})
REPS = 3
os.makedirs(OUT, exist_ok=True)

GSTACK_CMD = {"S1": "/plan-eng-review ", "S2": "/office-hours ", "S3": "/office-hours ", "S4": "/plan-eng-review "}
CONDITIONS = dict(v1.CONDITIONS)
CONDITIONS["gstack_cmd"] = dict(setup=v1.setup_gstack, prefix=GSTACK_CMD)

# v1의 실행 함수를 그대로 쓰되, 환경·설정·결과 폴더만 바꾼다
os.environ["CLAUDE_CONFIG_DIR"] = CLEAN_CONFIG
v1.OUT = OUT
_orig_run = v1.subprocess.run


def _run(cmd, **kw):
    cmd = list(cmd)
    i = cmd.index("--settings")
    cmd[i + 1] = SETTINGS
    return _orig_run(cmd, **kw)


v1.subprocess.run = _run


def run_one(key):
    sit, cname, rep = key.split("_", 1)[0], key.split("_", 1)[1].rsplit("_r", 1)[0], key.rsplit("_r", 1)[1]
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    s, cond = v1.SITUATIONS[sit], CONDITIONS[cname]
    cwd = os.path.join(CWDS, key)
    shutil.rmtree(cwd, ignore_errors=True)
    if s["fixture"]:
        shutil.copytree(v1.FIXTURE, cwd)
    else:
        os.makedirs(cwd)
    if cond.get("setup"):
        cond["setup"](cwd)
    prompt = cond.get("prefix", {}).get(sit, "") + s["prompt"]
    before = v1.snapshot(cwd)
    t1 = v1.run_turn(cwd, cond, prompt, key, 1)
    rec = dict(situation=sit, condition=cname, rep=int(rep), model=v1.MODEL, prompt=prompt, turn1=t1,
               asked=v1.asked_question(t1), turn2=None)
    # v1은 "?"로 끝날 때만 답했지만 선택지(A~D)형 질문을 놓쳐서, 모든 조건에 똑같이 답변지를 한 번 보낸다
    if t1["session"]:
        rec["turn2"] = v1.run_turn(cwd, cond, s["answer"], key, 2, resume=t1["session"])
    rec["new_files"] = sorted(v1.snapshot(cwd) - before)
    total = {k: 0 for k in ("input", "cache_create", "cache_read", "output")}
    for t in (t1, rec["turn2"]):
        if t:
            for k, v in v1.tokens(t["usage"]).items():
                total[k] += v
    rec["tokens"] = total
    rec["sec"] = round(t1["sec"] + (rec["turn2"]["sec"] if rec["turn2"] else 0), 1)
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: 끝 ({rec['sec']}초, 질문={rec['asked']}, 출력={total['output']})"


if __name__ == "__main__":
    keys = sys.argv[1:] or [f"{s}_{c}_r{r}" for r in range(1, REPS + 1) for c in CONDITIONS for s in v1.SITUATIONS]
    with ThreadPoolExecutor(max_workers=4) as ex:
        for msg in ex.map(run_one, keys):
            print(msg, flush=True)
