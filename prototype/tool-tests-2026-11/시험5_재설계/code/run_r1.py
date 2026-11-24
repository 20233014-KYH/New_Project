#!/usr/bin/env python3
"""R1: trailofbits variant-analysis가 맡는 상황 — "버그 하나 찾았는데, 같은 원인이 또 있나?" + 다시 쓸 semgrep 규칙 만들기.

- 과제 코드: make_fixture_r1.py (숨은 변종 8곳 + 안전한 코드 7곳, 파일 27개)
- 조건: nat 도구 없음 / tob trailofbits 전체 설치만 / tob_named 설치 + 스킬 이름을 불러 줌
- 허용: 읽기·쓰기(규칙 파일)·Task·Skill + semgrep 명령만. 인터넷 막음. 깨끗한 환경은 시험 3 v3와 같음.
- 채점(AI 채점 없음):
  1) 답의 '취약 목록:' 아래 함수 이름 → 8곳 중 찾은 수, 안전한 코드를 취약하다고 적은 수(헛경보)
  2) 만든 rules/*.yaml을 semgrep으로 실제 실행 → 과제 코드에서 잡은 변종 수·헛경보, 따로 둔 새 코드(holdout)에서 잡은 수·헛경보
사용법: python run_r1.py run [키 ...] | score
"""
import ast
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
import make_fixture_r1 as fx  # noqa: E402

v1 = v3.v1
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results_r1")
CWDS = os.path.join(HERE, "_cwd_r1")
VENV = os.path.normpath(os.path.join(HERE, "..", ".venv", "Scripts"))
SEMGREP = os.path.join(VENV, "semgrep.exe")
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
v1.ALLOWED = "Read,Glob,Grep,Write,Edit,Skill,TodoWrite,Task,Bash(semgrep *)"
v1.DENIED = "WebFetch,WebSearch,PowerShell"
os.environ["PATH"] = VENV + os.pathsep + os.environ["PATH"]
os.environ["SEMGREP_SEND_METRICS"] = "off"

# 큰 과제라 최대 턴을 40 → 80으로 늘린다(시험 3 장치의 subprocess.run 감싸기 위에 한 겹 더)
_prev = v1.subprocess.run


def _run(cmd, **kw):
    cmd = list(cmd)
    if "--max-turns" in cmd:
        cmd[cmd.index("--max-turns") + 1] = "80"
    return _prev(cmd, **kw)


v1.subprocess.run = _run

PROMPT = ("clubapp/auth/login.py의 find_user에서 SQL 주입 취약점을 찾았어(사용자 이름을 SQL 문자열에 그대로 붙임). "
          "이 저장소에 같은 원인의 문제가 또 있는지 빠짐없이 찾아 줘. 코드는 고치지 마. "
          "그리고 앞으로 새 코드에서도 같은 문제를 잡을 수 있게 semgrep 규칙을 rules/sqli.yaml 파일로 만들어 줘"
          "(semgrep 명령을 써서 확인해도 돼). "
          "마지막에 '취약 목록:' 줄 아래에 찾은 곳을 한 줄에 하나씩 `파일경로:함수이름` 형식으로 적어 줘(find_user 포함).")
TOB = plugin_dirs("trailofbits_skills")
CONDITIONS = {
    "nat": dict(prompt=PROMPT),
    "tob": dict(prompt=PROMPT, plugins=TOB),
    "tob_named": dict(prompt="trailofbits의 variant-analysis 스킬을 써서 해 줘. " + PROMPT, plugins=TOB),
}


def func_map(path):
    """줄 번호 → 그 줄을 감싸는 함수 이름."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    spans = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            spans.append((n.lineno, n.end_lineno, n.name))

    def at(line):
        best = None
        for a, b, name in spans:
            if a <= line <= b and (best is None or a > best[0]):
                best = (a, name)
        return best[1] if best else None
    return at


def semgrep_hits(rule_files, target):
    """규칙을 실제로 돌려 걸린 함수 이름 집합을 돌려준다. 규칙이 깨졌으면 None."""
    args = [SEMGREP, "--json", "--metrics=off", "--disable-version-check", "--quiet"]
    for r in rule_files:
        args += ["--config", r]
    p = subprocess.run(args + [target], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    try:
        d = json.loads(p.stdout)
    except Exception:
        return None, p.stderr[-300:]
    if d.get("errors") and not d.get("results"):
        return None, json.dumps(d["errors"])[:300]
    names = set()
    for res in d.get("results", []):
        fn = func_map(res["path"])(res["start"]["line"])
        if fn:
            names.add(fn)
    return names, None


def make_repo(cwd):
    shutil.rmtree(cwd, ignore_errors=True)
    fx.write(cwd)


def run_one(key):
    cname, rep = key.rsplit("_r", 1)
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    cond = CONDITIONS[cname]
    cwd = os.path.join(CWDS, key)
    make_repo(cwd)
    t = v1.run_turn(cwd, cond, cond["prompt"], key, 1)
    u = v1.tokens(t["usage"])
    # 만든 규칙을 보관하고, 깨끗한 과제 코드·따로 둔 새 코드에 실제로 돌린다
    rules = sorted(glob.glob(os.path.join(cwd, "rules", "*.y*ml")))
    keep = os.path.join(OUT, f"{key}_rules")
    shutil.rmtree(keep, ignore_errors=True)
    rule_eval = None
    if rules:
        os.makedirs(keep)
        for r in rules:
            shutil.copy(r, keep)
        rule_eval = eval_rules(key)
    rec = dict(condition=cname, rep=int(rep), turn=t, rule_eval=rule_eval,
               tokens=dict(total_in=u["input"] + u["cache_create"] + u["cache_read"], output=u["output"]))
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: 끝 ({t['sec']}초, rc={t['rc']}, 출력={u['output']}, 스킬={t['skills']}, 규칙={'있음' if rules else '없음'})"


def eval_rules(key):
    kept = sorted(glob.glob(os.path.join(OUT, f"{key}_rules", "*")))
    clean = os.path.join(CWDS, f"{key}_clean")
    hold = os.path.join(CWDS, f"{key}_hold")
    shutil.rmtree(clean, ignore_errors=True)
    shutil.rmtree(hold, ignore_errors=True)
    fx.write(clean)
    fx.write_holdout(hold)
    fix_hits, err1 = semgrep_hits(kept, clean)
    hold_hits, err2 = semgrep_hits(kept, hold)
    return dict(fixture=sorted(fix_hits) if fix_hits is not None else None,
                holdout=sorted(hold_hits) if hold_hits is not None else None, error=err1 or err2)


def listed(text):
    """'취약 목록:' 아래에 적힌 함수 이름들."""
    i = text.rfind("취약 목록")
    if i < 0:
        return None
    names = set()
    for line in text[i:].splitlines()[1:]:
        m = re.search(r"\.py\s*[:：]\s*(?:\w+\.)?(\w+)", line)
        if m:
            names.add(m.group(1))
    return names


def score():
    rows = {}
    for f in sorted(glob.glob(os.path.join(OUT, "*_r?.json"))):
        r = json.load(open(f, encoding="utf-8"))
        t = r["turn"]
        names = listed(t.get("result") or "")
        if names is None:
            names = listed("\n".join(t["texts"])) or set()
        found = sorted(set(fx.TRUTH) & names)
        fp = sorted(set(fx.DECOYS) & names)
        re_ = r.get("rule_eval") or {}
        fx_hits = set(re_.get("fixture") or [])
        ho_hits = set(re_.get("holdout") or [])
        rule = ("없음" if not r.get("rule_eval") else
                f"깨짐({re_.get('error')})" if re_.get("fixture") is None else
                f"과제 {len(set(fx.TRUTH) & fx_hits)}/8 헛{len(set(fx.DECOYS) & fx_hits)} · "
                f"새코드 {len(set(fx.HOLD_TRUTH) & ho_hits)}/3 헛{len(set(fx.HOLD_SAFE) & ho_hits)}")
        rows.setdefault(r["condition"], []).append(dict(
            found=len(found), fp=len(fp), miss=sorted(set(fx.TRUTH) - names), fpn=fp, rule=rule,
            tok=r["tokens"]["total_in"] + r["tokens"]["output"], sec=t["sec"], rc=t["rc"], skills=t.get("skills")))
    for c, xs in rows.items():
        print(f"\n[{c}]")
        for x in xs:
            print(f"  찾음 {x['found']}/8 헛경보 {x['fp']}  규칙: {x['rule']}  토큰 {x['tok']:,} 시간 {x['sec']}초 rc {x['rc']} 스킬 {x['skills']}")
            if x["miss"]:
                print(f"     놓침 {x['miss']}")
            if x["fpn"]:
                print(f"     헛경보 {x['fpn']}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        keys = sys.argv[2:] or [f"{c}_r{r}" for r in range(1, 4) for c in CONDITIONS]
        with ThreadPoolExecutor(max_workers=3) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
