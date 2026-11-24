#!/usr/bin/env python3
"""시험 3: 상황별 기획 시험. 같은 기획 요청을 도구 조건별로 따로 실행해서 기록한다.

- 상황 4개(S1 작은 수정, S2 큰 새 프로젝트, S3 목적이 흐릿함, S4 기존 코드에 기능 추가) x 조건 4개
  (none 도구 없음 / plan 기본 계획 모드 / sp superpowers / gstack)
- 매 실행은 새 폴더에서 시작한다. 사용자 설정은 읽지 않고(--setting-sources project) 도구만 이 실행에 불러온다.
- 권한은 좁게: 명령 실행(Bash)과 인터넷은 막고, 읽기·검색과 시험 폴더 안 문서 쓰기만 허용한다.
- 첫 응답이 질문으로 끝나면, 미리 정한 답변지로 한 번 더 대답한다(--resume).
- 결과: results/<상황>_<조건>.json, 실행 기록 results/<상황>_<조건>_t<턴>.jsonl
사용법: python run_plan_test.py [상황_조건 ...]   (없으면 전부, 이미 한 것은 건너뜀)
"""
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")
CWDS = os.path.join(HERE, "_cwd")
FIXTURE = os.path.join(HERE, "fixture_todo")
REPOS = r"C:\Users\User\Desktop\오픈소스_팀플\prototype\pilot_judgment\measure36\repos"
CLAUDE = os.path.expanduser("~/.local/bin/claude.exe")
MODEL = "sonnet"
ALLOWED = "Read,Glob,Grep,Write,Edit,Skill,TodoWrite,Task,ExitPlanMode"
DENIED = "Bash,WebFetch,WebSearch"
os.makedirs(OUT, exist_ok=True)

TAIL = " 코드는 아직 쓰지 말고, 개발 계획만 세워 줘."
SITUATIONS = {
    "S1": dict(fixture=True, prompt="이 할 일 앱에서 할 일을 삭제하기 전에 '정말 삭제할까요? (y/n)'를 묻게 하고 싶어." + TAIL,
               answer="기존 방식 그대로 하면 돼. 더 묻지 말고 계획을 마무리해 줘."),
    "S2": dict(fixture=False, prompt="동아리 회원 관리 웹 서비스를 처음부터 만들려고 해. 회원가입·로그인, 회비 납부 기록, 관리자 화면이 필요해." + TAIL,
               answer="팀 3명, 6주, Spring Boot + MySQL + React, 회원은 50명 정도야. 더 묻지 말고 계획을 마무리해 줘."),
    "S3": dict(fixture=False, prompt="우리 학과 학생들한테 도움이 되는 앱을 하나 만들고 싶어." + TAIL,
               answer="대상은 1~2학년이고, 수강신청 때 선수과목과 졸업요건을 파악하기 어려운 게 문제야. 팀 3명, 6주, 웹으로 할 거야. 더 묻지 말고 계획을 마무리해 줘."),
    "S4": dict(fixture=True, prompt="이 할 일 앱에 태그 기능을 넣고, 태그로 할 일을 걸러 보는 기능도 추가하고 싶어." + TAIL,
               answer="기존 데이터는 그대로 읽혀야 해. 더 묻지 말고 계획을 마무리해 줘."),
}


def setup_gstack(cwd):
    # 측정 때와 같은 방식: setup 스크립트가 하는 스킬 등록을 프로젝트 범위로 재현(브라우저 빌드는 안 함)
    root = os.path.join(REPOS, "garrytan_gstack")
    dst = os.path.join(cwd, ".claude", "skills")
    os.makedirs(dst, exist_ok=True)
    shutil.copytree(root, os.path.join(dst, "gstack"), ignore=shutil.ignore_patterns(".git", "node_modules"), dirs_exist_ok=True)
    for n in os.listdir(root):
        if os.path.isfile(os.path.join(root, n, "SKILL.md")):
            os.makedirs(os.path.join(dst, n), exist_ok=True)
            shutil.copy(os.path.join(root, n, "SKILL.md"), os.path.join(dst, n, "SKILL.md"))


CONDITIONS = {
    "none": dict(),
    "plan": dict(mode="plan"),
    "sp": dict(plugins=[os.path.join(REPOS, "obra_superpowers")]),
    "gstack": dict(setup=setup_gstack),
}


def snapshot(cwd):
    files = set()
    for root, dirs, names in os.walk(cwd):
        dirs[:] = [d for d in dirs if d not in (".claude", ".git", "__pycache__")]
        for n in names:
            files.add(os.path.relpath(os.path.join(root, n), cwd))
    return files


def run_turn(cwd, cond, prompt, name, turn, resume=None):
    cmd = [CLAUDE, "-p", prompt, "--setting-sources", "project", "--settings", "{}", "--strict-mcp-config",
           "--output-format", "stream-json", "--verbose", "--model", MODEL, "--max-turns", "40",
           "--permission-mode", cond.get("mode", "acceptEdits"),
           "--allowedTools", ALLOWED, "--disallowedTools", DENIED]
    for p in cond.get("plugins", []):
        cmd += ["--plugin-dir", p]
    if resume:
        cmd += ["--resume", resume]
    t0 = time.time()
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1500)
    open(os.path.join(OUT, f"{name}_t{turn}.jsonl"), "w", encoding="utf-8").write(r.stdout)
    info = dict(sec=round(time.time() - t0, 1), rc=r.returncode, stderr=r.stderr[-300:], skills=[], reads=[], writes=[],
                texts=[], denied=[], session=None, result=None, usage={}, turns=None, plugins=None, skill_count=None)
    for line in r.stdout.splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        t, st = e.get("type"), e.get("subtype")
        if t == "system" and st == "init":
            info["session"] = e.get("session_id")
            info["plugins"] = [p.get("name") for p in e.get("plugins", [])]
            info["skill_count"] = len(e.get("skills", []) or [])
        elif t == "assistant":
            for c in (e.get("message") or {}).get("content", []):
                if c.get("type") == "text":
                    info["texts"].append(c.get("text", ""))
                elif c.get("type") == "tool_use":
                    inp = c.get("input") or {}
                    if c.get("name") == "Skill":
                        info["skills"].append(inp.get("skill"))
                    elif c.get("name") == "Read":
                        info["reads"].append(inp.get("file_path"))
                    elif c.get("name") in ("Write", "Edit"):
                        info["writes"].append(inp.get("file_path"))
                    elif c.get("name") == "ExitPlanMode":
                        info["texts"].append(inp.get("plan", ""))
        elif t == "result":
            info["result"] = e.get("result")
            info["usage"] = e.get("usage") or {}
            info["turns"] = e.get("num_turns")
            info["session"] = e.get("session_id") or info["session"]
            info["denied"] = [d.get("tool_name") for d in (e.get("permission_denials") or [])]
    return info


def asked_question(info):
    tail = (info.get("result") or (info["texts"][-1] if info["texts"] else ""))[-400:]
    return "?" in tail


def tokens(u):
    return dict(input=u.get("input_tokens", 0), cache_create=u.get("cache_creation_input_tokens", 0),
                cache_read=u.get("cache_read_input_tokens", 0), output=u.get("output_tokens", 0))


def run_one(key):
    sit, cname = key.split("_", 1)
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    s, cond = SITUATIONS[sit], CONDITIONS[cname]
    cwd = os.path.join(CWDS, key)
    shutil.rmtree(cwd, ignore_errors=True)
    if s["fixture"]:
        shutil.copytree(FIXTURE, cwd)
    else:
        os.makedirs(cwd)
    if cond.get("setup"):
        cond["setup"](cwd)
    before = snapshot(cwd)
    t1 = run_turn(cwd, cond, s["prompt"], key, 1)
    rec = dict(situation=sit, condition=cname, model=MODEL, prompt=s["prompt"], turn1=t1, asked=asked_question(t1), turn2=None)
    if rec["asked"] and t1["session"]:
        rec["turn2"] = run_turn(cwd, cond, s["answer"], key, 2, resume=t1["session"])
    rec["new_files"] = sorted(snapshot(cwd) - before)
    total = {k: 0 for k in ("input", "cache_create", "cache_read", "output")}
    for t in (t1, rec["turn2"]):
        if t:
            for k, v in tokens(t["usage"]).items():
                total[k] += v
    rec["tokens"] = total
    rec["sec"] = round(t1["sec"] + (rec["turn2"]["sec"] if rec["turn2"] else 0), 1)
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: 끝 ({rec['sec']}초, 질문={rec['asked']}, 출력={total['output']})"


if __name__ == "__main__":
    keys = sys.argv[1:] or [f"{s}_{c}" for c in CONDITIONS for s in SITUATIONS]
    with ThreadPoolExecutor(max_workers=4) as ex:
        for msg in ex.map(run_one, keys):
            print(msg, flush=True)
