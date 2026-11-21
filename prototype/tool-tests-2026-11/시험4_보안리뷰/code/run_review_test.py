#!/usr/bin/env python3
"""시험 4-3: 코드 리뷰. 브랜치에 심어 둔 로직 버그 3개를 찾나 (보안 문제 아님).

- 심은 것: average_fee 빈 목록이면 0으로 나눔(설명은 0 반환) / paginate 1부터 시작인데 page*size라 한 페이지 밀림 /
  dedupe_members 이메일이 아니라 이름으로 중복 판단(동명이인 사라짐). unpaid_members는 문제없음.
- 조건: nat 자연어 리뷰 요청 / builtin 기본 /code-review
  (open-code-review 위임 모드는 별도 CLI(ocr) 설치가 필요해 이번엔 뺌)
- 저장소 구성·깨끗한 환경·git만 허용은 run_sec_test.py와 같음
사용법: python run_review_test.py run [키 ...] | score
"""
import glob
import json
import os
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor

import run_sec_test as sec

v1 = sec.v1
HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixture_review")
OUT = os.path.join(HERE, "..", "results_review")
CWDS = os.path.join(HERE, "_cwd_review")
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT

CONDITIONS = {
    "nat": "이 브랜치에서 바뀐 코드를 리뷰해 줘. 버그나 문제를 찾아 줘. 고치지는 말고 찾은 것만 알려 줘.",
    "builtin": "/code-review",
}


def make_repo(cwd):
    origin = cwd + "_origin.git"
    for d in (cwd, origin):
        shutil.rmtree(d, ignore_errors=True)
    os.makedirs(cwd)
    shutil.copy(os.path.join(FIX, "fees_base.py"), os.path.join(cwd, "fees.py"))
    sec.git(cwd, "init", "-q", "-b", "main")
    sec.git(cwd, "add", "-A")
    sec.git(cwd, "commit", "-qm", "회비 합계")
    sec.git(cwd, "init", "-q", "--bare", origin)
    sec.git(cwd, "remote", "add", "origin", origin)
    sec.git(cwd, "push", "-q", "origin", "main")
    sec.git(cwd, "remote", "set-head", "origin", "main")
    sec.git(cwd, "checkout", "-q", "-b", "feature/fee-helpers")
    shutil.copy(os.path.join(FIX, "fees_feature.py"), os.path.join(cwd, "fees.py"))
    sec.git(cwd, "add", "-A")
    sec.git(cwd, "commit", "-qm", "평균·페이지·중복 제거·미납자 함수 추가")


def run_one(key):
    cname, rep = key.rsplit("_r", 1)
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    cwd = os.path.join(CWDS, key)
    make_repo(cwd)
    t = v1.run_turn(cwd, {}, CONDITIONS[cname], key, 1)
    u = v1.tokens(t["usage"])
    rec = dict(condition=cname, rep=int(rep), turn=t, tokens=dict(total_in=u["input"] + u["cache_create"] + u["cache_read"], output=u["output"]))
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: 끝 ({t['sec']}초, rc={t['rc']}, 출력={u['output']})"


def score():
    for cname in CONDITIONS:
        rows = []
        for f in sorted(glob.glob(os.path.join(OUT, f"{cname}_r?.json"))):
            r = json.load(open(f, encoding="utf-8"))
            text = (r["turn"].get("result") or "") + "\n".join(r["turn"]["texts"])
            c = {
                "0으로 나눔": 1 if re.search(r"ZeroDivision|0으로 나누|빈 (목록|리스트)|len\(payments\)\s*==\s*0|empty", text, re.I) else 0,
                # 기본 /code-review는 영어로 답해서 영어 표현도 함께 본다(처음엔 한국어 위주라 맞힌 것을 놓쳤음)
                "페이지 한 칸 밀림": 1 if re.search(r"page\s*-\s*1|off.by.one|첫 (번째 )?페이지|1부터|건너뛰|1-based|first page|skips", text, re.I) else 0,
                "이름으로 중복 판단": 1 if re.search(r"(이름|name).{0,40}(이메일|email)|동명이인|같은 이름|이름이 같은|same name", text, re.I) else 0,
            }
            rows.append((sum(c.values()), r["tokens"]["total_in"] + r["tokens"]["output"], r["turn"]["sec"], r["turn"]["rc"],
                         [k for k, v in c.items() if not v], r["turn"]["skills"]))
        print(f"{cname:<8} 찾은 수 {[x[0] for x in rows]}/3  토큰 {[x[1] for x in rows]}  시간 {[x[2] for x in rows]}  rc {[x[3] for x in rows]}  "
              f"놓침 {[x[4] for x in rows]}  스킬 {[x[5] for x in rows]}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        keys = sys.argv[2:] or [f"{c}_r{r}" for r in range(1, 4) for c in CONDITIONS]
        with ThreadPoolExecutor(max_workers=3) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
