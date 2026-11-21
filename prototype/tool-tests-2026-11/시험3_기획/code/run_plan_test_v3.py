#!/usr/bin/env python3
"""시험 3 빡빡하게(v3): 어려운 상황 4개 x 조건 5개 x 3번, 깨끗한 환경.

v2와 달라진 점
- 상황: 이미 만점이 나온 쉬운 상황(S1 작은 수정, S4 작은 기존 코드)을 빼고 어려운 상황 2개를 넣음
  S2 큰 새 프로젝트 / S3 목적이 흐릿함 / S5 욕심 많은 요구(혼자·1주·카드 결제·개인정보) / S6 꼬인 기존 코드(명령줄·웹 두 군데)
- gstack을 실제처럼 사용자 폴더(시험용 설정 폴더의 skills/)에 설치. v2에서는 시험 폴더 안에 복사해서
  Claude가 앱 코드를 못 찾는 일이 생겼다. 다른 조건에 섞이지 않게 단계를 나눠 돌린다.
- gstack_cmd는 모든 상황에서 /office-hours를 부른다(v2의 /plan-eng-review는 이미 있는 계획을 검토하는 명령이었음)
사용법: python run_plan_test_v3.py base | install | gstack | uninstall
"""
import json
import os
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import run_plan_test as v1

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results_v3")
CWDS = os.path.join(HERE, "_cwd_v3")
CLEAN_CONFIG = os.path.expanduser("~/.claude-clean")
SKILLS = os.path.join(CLEAN_CONFIG, "skills")
SETTINGS = json.dumps({"claudeMdExcludes": ["**/.claude/CLAUDE.md", "C:/Users/User/.claude/CLAUDE.md"]})
REPS = 3
os.makedirs(OUT, exist_ok=True)

TAIL = v1.TAIL
SITUATIONS = {
    "S2": dict(v1.SITUATIONS["S2"], fixture=None),
    "S3": dict(v1.SITUATIONS["S3"], fixture=None),
    "S5": dict(fixture=None,
               prompt="혼자서 일주일 안에 동아리 회원 관리 웹을 만들어서 다음 주 행사 때 바로 쓰고 싶어. "
                      "회원가입, 회비 카드 결제, 출석 QR 체크, 공지 푸시 알림까지 다 넣고, 회원 전화번호와 학번도 받아야 해." + TAIL,
               answer="예산은 0원이고, 회원은 40명, 나는 파이썬만 조금 할 줄 알아. 더 묻지 말고 계획을 마무리해 줘."),
    "S6": dict(fixture=os.path.join(HERE, "fixture_tangled"),
               prompt="이 할 일 앱에 마감일을 넣고, 마감이 지난 할 일을 따로 볼 수 있게 하고 싶어." + TAIL,
               answer="명령줄과 웹 둘 다에서 보여야 하고, 기존 데이터는 그대로 읽혀야 해. 더 묻지 말고 계획을 마무리해 줘."),
}
CONDITIONS = {
    "none": dict(),
    "plan": dict(mode="plan"),
    "sp": dict(plugins=[os.path.join(v1.REPOS, "obra_superpowers")]),
    "gstack": dict(),
    "gstack_cmd": dict(prefix="/office-hours "),
}
PHASES = {"base": ["none", "plan", "sp"], "gstack": ["gstack", "gstack_cmd"]}

os.environ["CLAUDE_CONFIG_DIR"] = CLEAN_CONFIG
v1.OUT = OUT
_orig_run = v1.subprocess.run


# gstack은 사용자 스킬 폴더에 설치되므로 그 단계에서는 사용자 설정도 읽는다(시험용 설정 폴더라 깨끗함).
# 처음에 project만 읽어서 gstack이 안 켜진 24번은 results_v3/_invalid_gstack_projectonly/에 옮겨 둠
SOURCES = "project"


def _run(cmd, **kw):
    cmd = list(cmd)
    if "--settings" not in cmd:  # Claude 실행이 아닌 명령(git 등)은 그대로
        return _orig_run(cmd, **kw)
    cmd[cmd.index("--settings") + 1] = SETTINGS
    cmd[cmd.index("--setting-sources") + 1] = SOURCES
    return _orig_run(cmd, **kw)


v1.subprocess.run = _run


def install_gstack():
    # gstack setup이 하는 일(사용자 스킬 폴더에 gstack과 스킬별 폴더 등록)을 시험용 설정 폴더에 재현
    root = os.path.join(v1.REPOS, "garrytan_gstack")
    os.makedirs(SKILLS, exist_ok=True)
    shutil.copytree(root, os.path.join(SKILLS, "gstack"), ignore=shutil.ignore_patterns(".git", "node_modules"), dirs_exist_ok=True)
    n = 0
    for name in os.listdir(root):
        if os.path.isfile(os.path.join(root, name, "SKILL.md")):
            os.makedirs(os.path.join(SKILLS, name), exist_ok=True)
            shutil.copy(os.path.join(root, name, "SKILL.md"), os.path.join(SKILLS, name, "SKILL.md"))
            n += 1
    print(f"gstack 설치: 스킬 {n}개 → {SKILLS}")


def uninstall_gstack():
    # 지우지 않고 옆으로 옮겨 둔다(다른 조건에 섞이지 않게)
    if os.path.isdir(SKILLS):
        dst = os.path.join(CLEAN_CONFIG, f"_skills_gstack_off_{int(time.time())}")
        shutil.move(SKILLS, dst)
        print("gstack 치움 →", dst)


def run_one(key):
    sit, rest = key.split("_", 1)
    cname, rep = rest.rsplit("_r", 1)
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    s, cond = SITUATIONS[sit], CONDITIONS[cname]
    cwd = os.path.join(CWDS, key)
    shutil.rmtree(cwd, ignore_errors=True)
    if s["fixture"]:
        shutil.copytree(s["fixture"], cwd, ignore=shutil.ignore_patterns("__pycache__"))
    else:
        os.makedirs(cwd)
    prompt = cond.get("prefix", "") + s["prompt"]
    before = v1.snapshot(cwd)
    t1 = v1.run_turn(cwd, cond, prompt, key, 1)
    rec = dict(situation=sit, condition=cname, rep=int(rep), model=v1.MODEL, prompt=prompt, turn1=t1,
               asked=v1.asked_question(t1), turn2=None)
    if t1["session"]:  # 모든 조건에 답변지를 한 번 똑같이 보낸다
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
    return f"{key}: 끝 ({rec['sec']}초, 출력={total['output']}, 스킬={t1['skill_count']})"


if __name__ == "__main__":
    phase = sys.argv[1]
    if phase == "install":
        install_gstack()
    elif phase == "uninstall":
        uninstall_gstack()
    else:
        if phase == "base" and os.path.isdir(SKILLS):
            sys.exit("시험용 설정 폴더에 skills/가 남아 있어요. uninstall 먼저")
        if phase == "gstack":
            SOURCES = "user,project"
        keys = [f"{s}_{c}_r{r}" for r in range(1, REPS + 1) for c in PHASES[phase] for s in SITUATIONS]
        with ThreadPoolExecutor(max_workers=4) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
