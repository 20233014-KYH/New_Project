#!/usr/bin/env python3
"""R4b: R4와 같은 아이디어를 '실제로 쓰듯' 여러 번 주고받기. /office-hours는 질문을 하나씩 던지며 다듬는 도구라,
R4처럼 답을 한 번만 주면 제 방식대로 못 돈다(첫 질문 '목표가 뭐냐'에 답을 못 받아 가벼운 모드로 감).
- 모든 조건에 같은 사실을 같은 순서로 5번에 나눠 준다(질문 내용과 상관없이). 마지막에 "정리해 줘".
- 조건: none / plan / sp / gstack_full(실제 설치 + /office-hours, gstack 스크립트만 명령 허용)
- 채점: R4의 8개 항목 + 받은 사실을 계획에 반영했나 2개(졸업생 책=공급 확보, 학기 초 2주 몰림=출시 시점)
사용법: python run_r4b.py base | gstack | score
"""
import glob
import json
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor

import run_r4 as r4

v3, v1 = r4.v3, r4.v1
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results_r4b")
CWDS = os.path.join(HERE, "_cwd_r4b")
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
PROMPT = r4.v3.SITUATIONS["S8"]["prompt"]
FACTS = [
    "A로 할게. 실제로 우리 학과에서 쓰이게 하고 싶어. 학과 학생은 300명 정도야.",
    "지금은 학과 단톡방에 '책 팝니다' 글을 올리는데 글이 금방 묻혀. 거래는 학기 초 2주에 몰려.",
    "선배들은 졸업하면서 책을 그냥 버리기도 해. 에브리타임 책방도 있는데 우리 학과 과목으로 찾기가 불편해.",
    "나랑 친구 2명이 만들고, 이번 학기(12주) 수업 과제야. 돈은 쓰고 싶지 않아.",
    "더 묻지 말고 지금까지 내용으로 계획을 정리해 줘.",
]
CONDS = {"none": dict(), "plan": dict(mode="plan"), "sp": dict(plugins=[os.path.join(v1.REPOS, "obra_superpowers")]),
         "gstack_full": dict(prefix="/office-hours ")}


def run_one(key):
    cname, rep = key.rsplit("_r", 1)
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    cond = CONDS[cname]
    cwd = os.path.join(CWDS, key)
    shutil.rmtree(cwd, ignore_errors=True)
    os.makedirs(cwd)
    turns = [v1.run_turn(cwd, cond, cond.get("prefix", "") + PROMPT, key, 1)]
    for i, fact in enumerate(FACTS, 2):
        if not turns[-1]["session"]:
            break
        turns.append(v1.run_turn(cwd, cond, fact, key, i, resume=turns[-1]["session"]))
    tok = sum(sum(v1.tokens(t["usage"]).values()) for t in turns)
    rec = dict(condition=cname, rep=int(rep), turns=turns, tokens=tok, sec=round(sum(t["sec"] for t in turns), 1),
               rcs=[t["rc"] for t in turns], denied=sum(len(t["denied"]) for t in turns))
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: 끝 ({rec['sec']}초, rc={rec['rcs']}, 막힌 도구={rec['denied']})"


def r4_checks(fake):
    # run_r4.checks와 같은 정규식을, 파일 기록 없이 글만으로 적용(파일 기록은 score에서 이미 합침)
    saved = r4.written
    r4.written = lambda p: ""
    try:
        return r4.checks("_", fake)
    finally:
        r4.written = saved


def score():
    has, written = r4.has, r4.written
    rows = {}
    for f in sorted(glob.glob(os.path.join(OUT, "*_r?.json"))):
        key = os.path.basename(f)[:-5]
        r = json.load(open(f, encoding="utf-8"))
        txt = ["\n".join(t["texts"]) + written(os.path.join(OUT, f"{key}_t{i}.jsonl")) for i, t in enumerate(r["turns"], 1)]
        c = r4_checks(dict(turn1=dict(texts=[txt[0]]), turn2=dict(texts=["\n".join(txt[1:])])))
        final = "\n".join(txt[-2:])  # 마지막 정리 대답(과 그 직전)
        c["졸업생 책으로 매물 확보"] = has(r"졸업.{0,40}(책|매물|기증|수거|확보)|(수거|기증).{0,20}졸업", final)
        c["학기 초 2주에 맞춘 출시"] = has(r"학기 ?초|개강.{0,20}(전|맞춰|2주)|2주.{0,20}(전|안에|몰)", final)
        rows.setdefault(r["condition"], []).append((sum(c.values()), [k for k, v in c.items() if not v], r["tokens"], r["sec"], r["rcs"]))
    for c, xs in rows.items():
        print(f"{c:<12} 점수 {[x[0] for x in xs]}/10  토큰 {[f'{x[2]:,}' for x in xs]}  시간 {[x[3] for x in xs]}  rc {[x[4] for x in xs]}")
        for x in xs:
            if x[1]:
                print(f"    놓침 {x[1]}")


if __name__ == "__main__":
    phase = sys.argv[1]
    if phase == "score":
        score()
    else:
        if phase == "gstack":
            v3.SOURCES = "user,project"
            v1.ALLOWED += (",Bash(~/.claude/skills/gstack/*),Bash(*/.claude/skills/gstack/*),Bash(eval *),Bash(SLUG=*),"
                           "Bash(GSTACK_STATE_ROOT=*),Bash(mkdir *),Bash(cat *),Bash(ls *),Bash(echo *),Bash(_*)")
            v1.DENIED = "WebFetch,WebSearch,PowerShell"
            os.environ["PATH"] = os.path.join(HERE, "..", "tools_bun", "node_modules", ".bin") + os.pathsep + os.environ["PATH"]
            names = ["gstack_full"]
        else:
            names = ["none", "plan", "sp"]
        keys = [f"{c}_r{r}" for r in range(1, 4) for c in names]
        with ThreadPoolExecutor(max_workers=3) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
