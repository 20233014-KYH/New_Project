#!/usr/bin/env python3
"""R4: gstack /office-hours가 맡는 상황 — "막연한 새 아이디어" (만들기 전에 캐묻고 다시 짜야 하는 경우).

- 상황 S8: "학과 중고 전공책 거래 앱을 만들고 싶어. 어떻게 시작하면 좋을까?" (이미 대안이 많고, 만들기 전에 확인할 게 많은 아이디어)
- 조건: none / plan(계획 모드) / sp(superpowers) / gstack_cmd(gstack 사용자 스킬 설치 + /office-hours)
- 시험 3 v3 장치를 그대로 씀(깨끗한 환경, 첫 대답 뒤 같은 답변지를 한 번 보냄)
- 채점(AI 채점 없음): 정해 둔 항목 8개가 대답에 있는지 정규식으로 확인
사용법: python run_r4.py base | gstack | score   (gstack 단계 전에 v3 install, 뒤에 uninstall)
"""
import glob
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, r"C:\Users\User\Desktop\오픈소스_팀플\시험3_기획\code")
import run_plan_test_v3 as v3  # noqa: E402
from score_v2 import has, written  # noqa: E402

v1 = v3.v1
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results_r4")
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
v3.OUT = OUT
v3.CWDS = os.path.join(HERE, "_cwd_r4")
v3.SITUATIONS = {
    "S8": dict(fixture=None,
               prompt="우리 학과 학생들끼리 중고 전공책을 사고팔 수 있는 앱을 만들고 싶어. 어떻게 시작하면 좋을까?" + v3.TAIL,
               answer="학과 학생은 300명 정도고, 지금은 학과 단톡방에 '책 팝니다' 글을 올려서 거래해. 더 묻지 말고 마무리해 줘."),
}
PHASES = {"base": ["none", "plan", "sp"], "gstack": ["gstack_cmd"]}


def checks(key, r):
    t1, t2 = r["turn1"], r["turn2"] or {}
    txt1 = "\n".join(t1["texts"]) + written(os.path.join(OUT, f"{key}_t1.jsonl"))
    txt2 = "\n".join(t2.get("texts", [])) + written(os.path.join(OUT, f"{key}_t2.jsonl"))
    allt = txt1 + "\n" + txt2
    return {
        "지금 방식·고통을 먼저 물음": has(r"(지금|현재).{0,40}(어떻게|방식|거래|사고팔).{0,40}\?|어떤 (문제|불편).{0,30}\?|불편.{0,30}\?", txt1),
        "이미 있는 대안 짚음": has(r"에브리타임|에타|당근|번개장터|중고나라|오픈채팅|단톡|기존 (서비스|앱|방식)|대안", allt),
        "만들기 전에 수요 확인": has(r"(만들기|개발|코딩) ?(전|前)|먼저 .{0,30}(검증|확인|시험)|수요|인터뷰|설문|가설", allt),
        "가장 작게 시작(노코드·시트 등)": has(r"구글 ?(폼|시트|스프레드)|노션|노코드|스프레드시트|웹 ?페이지 ?하나|최소|MVP|가장 작", allt),
        # 처음 규칙은 '닭과 달걀·초기 매물'만 봐서 gstack의 "공급은 이미 있다 / 판매자와 구매자 중 누구부터 모을지" 같은 표현을 놓쳤다 → 모든 조건에 넓혀 다시 채점
        "판매자·구매자 동시 확보 문제": has(r"닭과 달걀|양면|콜드 ?스타트|cold ?start|초기 (물량|매물|사용자)|매물.{0,20}(부족|확보)|"
                                  r"판매자.{0,30}구매자.{0,30}(동시|모두|둘 다|누구부터)|공급(은|이|원| 확보| 쪽| 문제)|누구부터 모", allt),
        "거래 위험(사기·결제·만남)": has(r"사기|안전 ?거래|직거래|대면|에스크로|결제.{0,20}(위험|분쟁)|분쟁", allt),
        "왜 우리 것을 써야 하나(차별점)": has(r"차별|왜 .{0,20}(써야|쓸|사용할)|강의 ?(목록|별)|수업 ?(목록|별)|과목별|학기별", allt),
        "성공 기준": has(r"지표|성공 (기준|여부)|몇 (권|건|명)|거래 (수|건수)|측정", allt),
    }


def score():
    rows = {}
    for f in sorted(glob.glob(os.path.join(OUT, "S8_*_r?.json"))):
        key = os.path.basename(f)[:-5]
        r = json.load(open(f, encoding="utf-8"))
        c = checks(key, r)
        tk = r["tokens"]
        rows.setdefault(r["condition"], []).append((sum(c.values()), [k for k, v in c.items() if not v],
                                                    tk["input"] + tk["cache_create"] + tk["cache_read"] + tk["output"], r["sec"]))
    for c, xs in rows.items():
        print(f"{c:<11} 점수 {[x[0] for x in xs]}/8  토큰 {[f'{x[2]:,}' for x in xs]}  시간 {[x[3] for x in xs]}")
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
        if phase == "gstack_full":
            # 처음 gstack 단계는 명령 실행이 막혀 gstack 시작 스크립트가 못 돌았다(degraded mode).
            # 형원 허락(끝나면 되돌림)으로 실제 ~/.claude/skills/gstack에 설치하고, gstack 스크립트·기본 파일 명령만 허용해 다시 돌린다.
            v3.SOURCES = "user,project"
            v3.CONDITIONS["gstack_full"] = dict(prefix="/office-hours ")
            PHASES["gstack_full"] = ["gstack_full"]
            v1.ALLOWED += (",Bash(~/.claude/skills/gstack/*),Bash(*/.claude/skills/gstack/*),Bash(eval *),Bash(SLUG=*),"
                           "Bash(GSTACK_STATE_ROOT=*),Bash(mkdir *),Bash(cat *),Bash(ls *),Bash(echo *),Bash(_*)")
            v1.DENIED = "WebFetch,WebSearch,PowerShell"
            os.environ["PATH"] = os.path.join(HERE, "..", "tools_bun", "node_modules", ".bin") + os.pathsep + os.environ["PATH"]
        keys = [f"S8_{c}_r{r}" for r in range(1, 4) for c in PHASES[phase]]
        with ThreadPoolExecutor(max_workers=3) as ex:
            for msg in ex.map(v3.run_one, keys):
                print(msg, flush=True)
