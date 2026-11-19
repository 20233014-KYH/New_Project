#!/usr/bin/env python3
"""시험 4-1: 보안 검사 비교. 브랜치에 심어 둔 보안 구멍 3개 + 안전한 코드 1개를 몇 개 찾나.

- 과제: app_base.py(main) → app_feature.py(작업 브랜치). 심은 것: SQL 주입(find_member), 명령 주입(export_report),
  경로 조작(read_attachment). 안전한 코드(search_by_email, 값 바인딩)를 문제라고 하면 헛경보.
- 조건: nat 도구 없이 자연어 / builtin 기본 /security-review / ccsr claude-code-security-review 명령 파일 설치 후 /security-review /
        tob trailofbits 스킬 모음 + 자연어
- 깨끗한 환경은 시험 3 v3와 같고, 명령 실행은 git만 허용. 한 번만 묻고 대답을 채점(AI 채점 없음, 정해진 규칙)
사용법: python run_sec_test.py run [키 ...] | score
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
import run_plan_test_v3 as v3  # noqa: E402  깨끗한 환경 설정을 그대로 씀
from run_plan_test_v4 import plugin_dirs  # noqa: E402

v1 = v3.v1
HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixture_sec")
OUT = os.path.join(HERE, "..", "results")
CWDS = os.path.join(HERE, "_cwd")
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
v1.ALLOWED = "Read,Glob,Grep,Skill,TodoWrite,Task,Bash(git:*)"
v1.DENIED = "Write,Edit,WebFetch,WebSearch"

NAT = "이 브랜치에서 바뀐 코드의 보안 문제를 검토해 줘. 고치지는 말고 찾은 문제만 알려 줘."
CONDITIONS = {
    "nat": dict(prompt=NAT),
    "builtin": dict(prompt="/security-review"),
    "ccsr": dict(prompt="/security-review", ccsr=True),
    "tob": dict(prompt=NAT, plugins=plugin_dirs("trailofbits_skills")),
}


def git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.com", *args], cwd=cwd,
                   capture_output=True, check=True)


def make_repo(cwd):
    origin = cwd + "_origin.git"
    for d in (cwd, origin):
        shutil.rmtree(d, ignore_errors=True)
    os.makedirs(cwd)
    shutil.copy(os.path.join(FIX, "app_base.py"), os.path.join(cwd, "app.py"))
    git(cwd, "init", "-q", "-b", "main")
    git(cwd, "add", "-A")
    git(cwd, "commit", "-qm", "회원 목록 서버")
    git(cwd, "init", "-q", "--bare", origin)
    git(cwd, "remote", "add", "origin", origin)
    git(cwd, "push", "-q", "origin", "main")
    git(cwd, "remote", "set-head", "origin", "main")
    git(cwd, "checkout", "-q", "-b", "feature/member-tools")
    shutil.copy(os.path.join(FIX, "app_feature.py"), os.path.join(cwd, "app.py"))
    git(cwd, "add", "-A")
    git(cwd, "commit", "-qm", "회원 찾기, 보고서 내보내기, 첨부 읽기 추가")


def run_one(key):
    cname, rep = key.rsplit("_r", 1)
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    cond = CONDITIONS[cname]
    cwd = os.path.join(CWDS, key)
    make_repo(cwd)
    if cond.get("ccsr"):
        d = os.path.join(cwd, ".claude", "commands")
        os.makedirs(d)
        shutil.copy(os.path.join(v1.REPOS, "anthropics_claude-code-security-review", ".claude", "commands", "security-review.md"), d)
    t = v1.run_turn(cwd, cond, cond["prompt"], key, 1)
    u = v1.tokens(t["usage"])
    rec = dict(condition=cname, rep=int(rep), turn=t, tokens=dict(total_in=u["input"] + u["cache_create"] + u["cache_read"], output=u["output"]))
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: 끝 ({t['sec']}초, 출력={u['output']}, rc={t['rc']}, 스킬={t['skill_count']})"


def has(p, s):
    return 1 if re.search(p, s, re.I | re.S) else 0


def decoy_flagged(text):
    # 안전한 search_by_email 근처에서 취약하다고 말했는지(안전하다는 말 없이)
    for m in re.finditer(r"search_by_email", text):
        win = text[max(0, m.start() - 200): m.end() + 200]
        if re.search(r"취약|vulnerab|injection|인젝션|주입", win, re.I) and not re.search(r"안전|safe|파라미터|parameteri|바인딩|placeholder|\?", win, re.I):
            return 1
    return 0


def score():
    by = {}
    for f in sorted(glob.glob(os.path.join(OUT, "*_r?.json"))):
        r = json.load(open(f, encoding="utf-8"))
        t = r["turn"]
        text = (t.get("result") or "") + "\n" + "\n".join(t["texts"])
        c = {
            "SQL 주입": has(r"SQL ?(injection|인젝션|주입)|SQLi", text),
            "명령 주입": has(r"(command|명령(어)?|커맨드|OS|셸|shell) ?(injection|인젝션|주입)|shell=True", text),
            "경로 조작": has(r"path traversal|경로 (조작|순회|탐색)|디렉(터|토)리 (순회|탐색|트래버설)|\.\./", text),
        }
        fp = decoy_flagged(text)
        by.setdefault(r["condition"], []).append((sum(c.values()), fp, r["tokens"]["total_in"] + r["tokens"]["output"], t["sec"], t["rc"], c))
    for cname, xs in by.items():
        print(f"{cname:<8} 찾은 수 {[x[0] for x in xs]}/3  헛경보 {[x[1] for x in xs]}  토큰 {min(x[2] for x in xs)}~{max(x[2] for x in xs)}  "
              f"시간 {[x[3] for x in xs]}  rc {[x[4] for x in xs]}")
        for x in xs:
            if x[0] < 3:
                print("    놓침:", [k for k, v in x[5].items() if not v])


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        keys = sys.argv[2:] or [f"{c}_r{r}" for r in range(1, 4) for c in CONDITIONS]
        with ThreadPoolExecutor(max_workers=4) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
