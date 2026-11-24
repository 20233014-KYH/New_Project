#!/usr/bin/env python3
"""R5: GSD·planning-with-files가 맡는 상황 — 여러 날(6 세션)에 걸친 작업에서 앞에서 '말로' 정한 규칙을 뒤에서도 지키나.

- 과제: 동아리 회비 계산기(fixture_r5, 거의 빈 폴더). 세션마다 새로 시작(--resume 없음, 대화 기억 없음, 폴더만 같음).
  세션 1에 규칙 4개(정수 금액·'[입력오류] ' 오류 메시지·이메일 소문자·메서드마다 테스트)를 말로만 알려 준다.
  세션 3에 새 규칙(면제 회원은 부과·미납·합계·내보내기에서 빠짐)을 말로만 알려 준다 → 2단계에서 만든 부과도 고쳐야 함.
  세션 4~6은 "다음 단계 해 줘: ○○"만 말한다(규칙을 다시 말하지 않음).
- 조건: none 도구 없음 / pwf planning-with-files(세션 1에 /planning-with-files:plan) /
        gsd gsd-core(세션 1에 /gsd-core:gsd:quick, 세션 2~6에 /gsd-core:gsd:resume-work) / sp superpowers(설치만)
- 채점(AI 채점 없음): 6 세션이 끝난 뒤 숨은 테스트(hidden_tests_r5.py, 16개)를 돌려 규칙 묶음별 통과 수. + 세션마다 자기 테스트 통과 여부.
사용법: python run_r5.py run [키 ...] | score
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, r"C:\Users\User\Desktop\오픈소스_팀플\시험3_기획\code")
import run_plan_test_v3 as v3  # noqa: E402
from run_plan_test_v4 import plugin_dirs  # noqa: E402

v1 = v3.v1
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results_r5")
CWDS = os.path.join(HERE, "_cwd_r5")
HIDDEN = os.path.join(HERE, "hidden_tests_r5.py")
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
v1.ALLOWED = ("Read,Glob,Grep,Write,Edit,Skill,TodoWrite,Task,"
              "Bash(python:*),Bash(python -m pytest:*),Bash(pytest:*),Bash(git:*),Bash(ls:*),Bash(cat:*),Bash(mkdir:*)")
v1.DENIED = "WebFetch,WebSearch,PowerShell"

_prev = v1.subprocess.run


def _run(cmd, **kw):
    cmd = list(cmd)
    if "--max-turns" in cmd:
        cmd[cmd.index("--max-turns") + 1] = "80"
    return _prev(cmd, **kw)


v1.subprocess.run = _run

S1 = ("동아리 회비 계산기를 만들 거야. 최종 기능은 회원 등록·목록, 월 회비 부과, 납부 기록, 미납자 목록, 월별 보고서, CSV 내보내기야. "
      "모두 `from dues import Club`의 Club 메서드로 만들어: add_member(name, email, exempt=False), members(), "
      "charge_month(month, amount), pay(email, month, amount), unpaid(month) → 이메일 목록, "
      "report(month) → {\"charged\", \"paid\", \"unpaid\"} 딕셔너리, export_csv(month, path). month는 'YYYY-MM' 형식이야. "
      "전체를 단계로 나눠 계획을 세우고, 오늘은 1단계(회원 등록·목록)만 구현하고 테스트까지 통과시켜 줘. 나머지는 다음 세션들에서 할 거야. "
      "앞으로 모든 단계에서 지킬 규칙이 있어: ① 금액은 전부 정수 원 단위(소수면 오류) ② 잘못된 입력은 ValueError를 내고 "
      "메시지는 '[입력오류] '로 시작 ③ 이메일은 소문자로 바꿔 저장·비교 ④ 공개 메서드마다 tests/에 테스트.")
SESSIONS = [
    S1,
    "다음 단계 해 줘: 월 회비 부과(charge_month). 테스트까지 통과시켜 줘.",
    ("다음 단계 해 줘: 납부 기록(pay). 그리고 오늘 동아리에서 정한 게 있어: 회비 면제 회원(exempt=True)은 회비를 부과하지 않고, "
     "미납 목록·합계·내보내기 어디에서도 빠져야 해. 앞으로도 계속 지켜야 해. 테스트까지 통과시켜 줘."),
    "다음 단계 해 줘: 미납자 목록(unpaid). 테스트까지 통과시켜 줘.",
    "다음 단계 해 줘: 월별 보고서(report). 테스트까지 통과시켜 줘.",
    "다음 단계 해 줘: CSV 내보내기(export_csv). 테스트까지 통과시켜 줘.",
]
CONDITIONS = {
    "none": dict(),
    "pwf": dict(plugins=plugin_dirs("OthmanAdi_planning-with-files"), first="/planning-with-files:plan "),
    "gsd": dict(plugins=plugin_dirs("open-gsd_gsd-core"), first="/gsd-core:gsd:quick ", rest="/gsd-core:gsd:resume-work "),
    # superpowers: 오래 유지할 코드·여러 단계 작업용(계획을 docs/에 남기고 TDD) — 사람들이 쓰는 방식대로 설치만 하고 같은 말로 시킴
    "sp": dict(plugins=[os.path.join(v1.REPOS, "obra_superpowers")]),
}


def pytest_run(cwd, *args):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *args], cwd=cwd, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=env, timeout=300)
    return r.returncode, r.stdout


def hidden(cwd):
    """숨은 테스트를 따로 이름으로 복사해 돌리고, 테스트별 통과 여부를 돌려준다."""
    dst = os.path.join(cwd, "_hidden_grade_test.py")
    shutil.copy(HIDDEN, dst)
    try:
        _, out = pytest_run(cwd, "_hidden_grade_test.py", "-rA")
    finally:
        os.remove(dst)
    res = {}
    for m in re.finditer(r"^(PASSED|FAILED|ERROR) _hidden_grade_test\.py::(\w+)", out, re.M):
        res[m.group(2)] = m.group(1) == "PASSED"
    return res, out[-600:]


def run_one(key):
    cname, rep = key.rsplit("_r", 1)
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    cond = CONDITIONS[cname]
    cwd = os.path.join(CWDS, key)
    # git의 읽기 전용 파일 때문에 그냥 지우면 남는다(재실행 때 그래서 멈춤) → 읽기 전용을 풀고 지운다
    shutil.rmtree(cwd, onexc=lambda f, p, e: (os.chmod(p, 0o700), f(p)))  if os.path.exists(cwd) else None
    shutil.copytree(os.path.join(HERE, "fixture_r5"), cwd)
    g = ["git", "-c", "user.name=test", "-c", "user.email=test@example.com"]
    subprocess.run(["git", "init", "-q"], cwd=cwd)
    subprocess.run(g + ["add", "-A"], cwd=cwd)
    subprocess.run(g + ["commit", "-qm", "start"], cwd=cwd)
    sessions = []
    for i, task in enumerate(SESSIONS, 1):
        prefix = cond.get("first", "") if i == 1 else cond.get("rest", "")
        t = v1.run_turn(cwd, cond, prefix + task, key, i)  # 매번 새 세션
        rc, _ = pytest_run(cwd)
        u = v1.tokens(t["usage"])
        sessions.append(dict(i=i, sec=t["sec"], rc=t["rc"], own_tests_ok=rc == 0, skills=t["skills"], turns=t["turns"],
                             tokens=u["input"] + u["cache_create"] + u["cache_read"] + u["output"], result=(t.get("result") or "")[-800:]))
    res, tail = hidden(cwd)
    notes = [p for p in glob.glob(os.path.join(cwd, "**", "*.md"), recursive=True)
             if "입력오류" in open(p, encoding="utf-8", errors="replace").read()]
    rec = dict(condition=cname, rep=int(rep), sessions=sessions, hidden=res, hidden_tail=tail,
               rule_notes=[os.path.relpath(p, cwd) for p in notes])
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: 숨은 테스트 {sum(res.values())}/{len(res) or 16}  세션별 자기테스트 {[s['own_tests_ok'] for s in sessions]}"


GROUPS = {"기능": "test_func_", "정수": "test_int_", "오류": "test_err_", "소문자": "test_lower_", "면제": "test_exempt_"}
GROUP_N = {"기능": 3, "정수": 3, "오류": 4, "소문자": 2, "면제": 4}


def score():
    for cname in CONDITIONS:
        print(f"\n[{cname}]")
        for f in sorted(glob.glob(os.path.join(OUT, f"{cname}_r?.json"))):
            r = json.load(open(f, encoding="utf-8"))
            h = r["hidden"]
            by = {gname: sum(1 for k, v in h.items() if k.startswith(p) and v) for gname, p in GROUPS.items()}
            tok = sum(s["tokens"] for s in r["sessions"])
            sec = sum(s["sec"] for s in r["sessions"])
            print(f"  숨은 {sum(h.values())}/16  " + "  ".join(f"{g} {by[g]}/{GROUP_N[g]}" for g in GROUPS) +
                  f"  자기테스트 {''.join('O' if s['own_tests_ok'] else 'X' for s in r['sessions'])}  토큰 {tok:,}  시간 {sec / 60:.0f}분  규칙메모 {r['rule_notes'][:3]}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        keys = sys.argv[2:] or [f"{c}_r{r}" for r in range(1, 4) for c in CONDITIONS]
        with ThreadPoolExecutor(max_workers=3) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
