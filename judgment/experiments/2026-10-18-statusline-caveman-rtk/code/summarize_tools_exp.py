#!/usr/bin/env python3
"""run_tools_exp.py 결과 집계: 조건별·과제별 평균과 기준(mine) 대비 변화."""
import glob
import json
import os
import statistics as st
import sys

sys.stdout.reconfigure(encoding="utf-8")
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "real_test", "tools_exp")
rows = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(D, "r*_*.json")))]
COMBOS = ["mine", "mine_cav", "mine_rtk", "mine_both"]
TASKS = ["tdd", "bugfix", "refactor"]


def ok(r):
    v = r["verify"]
    return v["passed"] and v["tests_untouched"] is not False and (r["task"] != "refactor" or v["committed"])


def avg(rs, k):
    return st.mean(r[k] for r in rs) if rs else 0


print(f"실행 {len(rows)}개\n")
print("조건 | 과제 | n | 성공 | 턴 | 입력토큰 | 출력토큰 | 시간 | 답글자 | rtk바꿈 | Bash/PS | 스킬")
for c in COMBOS:
    for t in TASKS + ["전체"]:
        rs = [r for r in rows if r["combo"] == c and (t == "전체" or r["task"] == t)]
        if not rs:
            continue
        bash = sum(r["tools"].get("Bash", 0) for r in rs)
        ps = sum(r["tools"].get("PowerShell", 0) for r in rs)
        sk = sorted({s for r in rs for s in r["skills"]})
        print(f"{c} | {t} | {len(rs)} | {sum(ok(r) for r in rs)}/{len(rs)} | {avg(rs,'num_turns'):.1f} | {avg(rs,'input_sum'):,.0f} | "
              f"{avg(rs,'output_tokens'):,.0f} | {avg(rs,'wall_s'):.1f} | {avg(rs,'result_chars'):.0f} | {sum(r['rtk_rewrites'] for r in rs)} | {bash}/{ps} | {sk}")

print("\n기준(mine) 대비 변화 (과제별 평균의 평균)")
for c in COMBOS[1:]:
    d = {}
    for k in ("input_sum", "output_tokens", "wall_s", "result_chars"):
        ratios = []
        for t in TASKS:
            b = [r for r in rows if r["combo"] == "mine" and r["task"] == t]
            x = [r for r in rows if r["combo"] == c and r["task"] == t]
            if b and x and avg(b, k):
                ratios.append(avg(x, k) / avg(b, k))
        d[k] = f"{(st.mean(ratios) - 1) * 100:+.0f}%" if ratios else "-"
    print(c, d)
