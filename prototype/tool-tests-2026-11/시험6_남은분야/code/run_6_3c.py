#!/usr/bin/env python3
"""시험 6-3c: codegraph 일반화 확인(Codex 제안) — 다른 흐름 질문 2개를 '시작점 줌(s) / 안 줌(n)'으로 짝지어 none vs codegraph.

문제·정답표: Codex가 코드에서 직접 뽑음(codex_상의/6-3c_문제_정답표.txt → 6-3c_questions.json), Claude가 함수 존재·호출 순서 확인.
 F1 = 관찰 프롬프트 만들기 흐름(정답 함수 6개), F2 = 플러그인 캐시 복사 대상 경로 계산 흐름(정답 함수 5개)
채점: 답에 나온 정답 함수 수 + 토큰(전체·새 토큰)·시간·읽은 파일.
사용법: python run_6_3c.py run [키 ...] | score     키 예: F1n_codegraph_2   (이미 있는 결과는 건너뜀)
"""
import glob
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import run_6_3b as b3

base, v1 = b3.base, b3.v1
HERE = base.HERE
OUT = os.path.join(HERE, "..", "results_6_3c")
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
v1.DENIED = "PowerShell,WebFetch,WebSearch,Write,Edit"
QS = {q["id"]: q for q in json.load(open(os.path.join(HERE, "6-3c_questions.json"), encoding="utf-8"))}
CONDS = ["none", "codegraph"]
TASKS = ["F1s", "F1n", "F2s", "F2n"]


def run_one(key):
    task, cname, rep = key.split("_")
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    q = QS[task[:2]]
    cwd = base.setup(cname)
    base._allow_by_cwd[cwd] = base.EXTRA_ALLOW[cname]
    base._mcp_by_cwd[cwd] = base.MCP.get(cname)
    prompt = (q["start_prompt"] if task.endswith("s") else q["nostart_prompt"]) + " 단계마다 파일 경로와 함수 이름을 적어 줘. 코드는 고치지 마."
    t = v1.run_turn(cwd, {}, prompt, key, 1)
    text = t.get("result") or "\n".join(t["texts"][-2:])
    calls, reads = b3.tool_stats(os.path.join(OUT, f"{key}_t1.jsonl"))
    found = [k for k in q["keys"] if re.search(r"\b" + k + r"\b", text)]
    u = v1.tokens(t["usage"])
    rec = dict(task=task, condition=cname, rep=int(rep), sec=t["sec"], rc=t["rc"], turns=t["turns"],
               tokens=u["input"] + u["cache_create"] + u["cache_read"] + u["output"], new_tokens=u["input"] + u["cache_create"] + u["output"],
               usage=u, calls=calls, reads=reads, found=found, score=len(found), total=len(q["keys"]), result=text[-2000:])
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: {len(found)}/{len(q['keys'])}  토큰 {rec['tokens']:,} (새 {rec['new_tokens']:,})  {t['sec']:.0f}초  읽은 파일 {reads}  전용 {b3.own_calls(calls)}번"


def score():
    for task in TASKS:
        print(f"== {task}")
        for cname in CONDS:
            rs = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(OUT, f"{task}_{cname}_?.json")))]
            if rs:
                n = len(rs)
                pts = [str(r["score"]) + "/" + str(r["total"]) for r in rs]
                print(f"[{cname}] 점수 {pts}  평균 토큰 {sum(r['tokens'] for r in rs) // n:,}  새 토큰 {sum(r['new_tokens'] for r in rs) // n:,}"
                      f"  평균 {sum(r['sec'] for r in rs) / n:.0f}초  읽은 파일 {[r['reads'] for r in rs]}  전용 {[b3.own_calls(r['calls']) for r in rs]}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        keys = sys.argv[2:] or [f"{t}_{c}_{r}" for r in range(1, 4) for t in TASKS for c in CONDS]
        with ThreadPoolExecutor(max_workers=2) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
