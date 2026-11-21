#!/usr/bin/env python3
"""시험 6-2: ③ 코드 검색 — "라이브러리 최신 사용법이 필요해요" (context7)

- 과제: Jackson 3(tools.jackson 3.1.7, 2025-10 새 메이저 — 패키지 이름·예외·빌더가 2.x와 다름)으로 Main.java 완성.
  fixture_6_2(그래들, 오프라인, 3.1.7만 받아 둠 → 2.x 코드는 컴파일이 안 됨).
- 조건: none = 도구 없음 / c7 = context7 MCP
- 방식: run = 그래들로 돌려 보며 고칠 수 있음(보통 쓰는 방식) / nc = 돌려 볼 수 없음(첫 답이 바로 맞나)
- 채점(AI 채점 없음): 끝난 뒤 깨끗이 다시 빌드·실행 → 컴파일, TOTAL, 고객별 합계, summary.json(들여쓰기) 4점.
  + 토큰, 시간, 그래들 실행 횟수(몇 번 고쳤나), context7 호출 수.
사용법: python run_6_2.py run [키 ...] | score     (이미 있는 결과는 건너뜀)
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, r"C:\Users\User\Desktop\오픈소스_팀플\시험3_기획\code")
import run_plan_test_v3 as v3  # noqa: E402

v1 = v3.v1
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results_6_2")
CWDS = os.path.join(HERE, "_cwd_6_2")
NPM = r"C:\Users\User\Desktop\오픈소스_팀플\prototype\pilot_judgment\measure36\npm\node_modules"
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
v1.ALLOWED = "Read,Glob,Grep,Write,Edit,TodoWrite"
v1.DENIED = "PowerShell,WebFetch,WebSearch"

_mcp_by_cwd, _allow_by_cwd, _lock = {}, {}, threading.Lock()
_prev = v1.subprocess.run


def _run(cmd, **kw):
    cmd = list(cmd)
    if "--max-turns" in cmd:
        cmd[cmd.index("--max-turns") + 1] = "60"
    cfg = _mcp_by_cwd.get(kw.get("cwd"))
    if "--strict-mcp-config" in cmd and cfg:
        cmd += ["--mcp-config", json.dumps({"mcpServers": cfg})]
    extra = _allow_by_cwd.get(kw.get("cwd"))
    if extra and "--allowedTools" in cmd:
        cmd[cmd.index("--allowedTools") + 1] += "," + extra
    return _prev(cmd, **kw)


v1.subprocess.run = _run

TASK = ("src/main/java/app/Main.java를 완성해 줘. JSON 라이브러리는 이미 넣어 둔 Jackson 3(tools.jackson, 3.1.7)만 써. "
        "orders.json을 읽어서 ① 결제 완료(status가 paid) 주문의 매출 합계(qty×price)를 `TOTAL=숫자` 한 줄로 출력하고 "
        "② 고객별 paid 매출을 고객 이름순으로 `kim=숫자`처럼 한 줄씩 출력하고 "
        "③ summary.json 파일에 {\"shop\": 가게 이름, \"total\": 합계, \"customers\": {고객: 합계}}를 들여쓰기(보기 좋게)해서 저장해. "
        "주문은 자바 record 클래스로 읽어(데이터 바인딩). orders.json에 모르는 필드(coupon 등)가 있어도 실패하면 안 돼. ")
RUN_TAIL = "`./gradlew run --offline -q`로 돌려 볼 수 있어(인터넷 없음)."
NC_TAIL = "지금은 빌드·실행을 할 수 없는 환경이야. 한 번에 컴파일되게 써 줘."
CONDS, MODES = ["none", "c7"], ["run", "nc"]


def gradle(cwd):
    shutil.rmtree(os.path.join(cwd, "build"), ignore_errors=True)
    if os.path.exists(os.path.join(cwd, "summary.json")):
        os.remove(os.path.join(cwd, "summary.json"))
    r = subprocess.run(["bash", "./gradlew", "run", "--offline", "-q"], cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600)
    return r.returncode, r.stdout, r.stderr


def grade(cwd):
    rc, out, err = gradle(cwd)
    g = dict(compiled=rc == 0, total="TOTAL=134000" in out, customers="kim=110000" in out and "park=24000" in out,
             summary=False, stdout=out[-400:], stderr=err[-800:])
    p = os.path.join(cwd, "summary.json")
    if os.path.exists(p):
        txt = open(p, encoding="utf-8").read()
        try:
            j = json.loads(txt)
            g["summary"] = (j.get("total") == 134000 and j.get("customers", {}).get("kim") == 110000
                            and j.get("shop") == "밤가이" and "\n" in txt.strip())
        except Exception:
            pass
    g["score"] = sum(g[k] for k in ("compiled", "total", "customers", "summary"))
    return g


def count(jsonl, pred):
    n = 0
    for line in open(jsonl, encoding="utf-8", errors="replace"):
        try:
            e = json.loads(line)
        except Exception:
            continue
        for c in (e.get("message") or {}).get("content", []) if e.get("type") == "assistant" else []:
            if c.get("type") == "tool_use" and pred(c):
                n += 1
    return n


def run_one(key):
    mode, cname, rep = key.split("_")
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    cwd = os.path.join(CWDS, key)
    shutil.rmtree(cwd, ignore_errors=True)
    shutil.copytree(os.path.join(HERE, "fixture_6_2"), cwd)
    with _lock:
        if cname == "c7":
            _mcp_by_cwd[cwd] = {"context7": {"command": "node", "args": [os.path.join(NPM, "@upstash", "context7-mcp", "dist", "index.js")]}}
        allow = ["mcp__context7"] if cname == "c7" else []
        if mode == "run":
            allow += ["Bash(./gradlew:*)", "Bash(bash ./gradlew:*)", "Bash(gradlew:*)"]
        _allow_by_cwd[cwd] = ",".join(allow)
    t = v1.run_turn(cwd, {}, TASK + (RUN_TAIL if mode == "run" else NC_TAIL), key, 1)
    g = grade(cwd)
    jl = os.path.join(OUT, f"{key}_t1.jsonl")
    u = v1.tokens(t["usage"])
    rec = dict(mode=mode, condition=cname, rep=int(rep), sec=t["sec"], rc=t["rc"], turns=t["turns"],
               tokens=u["input"] + u["cache_create"] + u["cache_read"] + u["output"], usage=u, grade=g,
               gradle_runs=count(jl, lambda c: c.get("name") == "Bash" and "gradlew" in (c.get("input") or {}).get("command", "")),
               c7_calls=count(jl, lambda c: c.get("name", "").startswith("mcp__context7")),
               main=open(os.path.join(cwd, "src", "main", "java", "app", "Main.java"), encoding="utf-8").read()[:3000],
               result=(t.get("result") or "")[-800:])
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: {g['score']}/4  토큰 {rec['tokens']:,}  {t['sec']:.0f}초  그래들 {rec['gradle_runs']}번  c7 {rec['c7_calls']}번"


def score():
    for mode in MODES:
        for cname in CONDS:
            rs = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(OUT, f"{mode}_{cname}_?.json")))]
            if rs:
                print(f"[{mode} {cname}] 점수 " + " / ".join(f"{r['grade']['score']}/4" for r in rs) +
                      f"  평균 토큰 {sum(r['tokens'] for r in rs) // len(rs):,}  평균 {sum(r['sec'] for r in rs) / len(rs):.0f}초"
                      f"  그래들 {[r['gradle_runs'] for r in rs]}  c7 {[r['c7_calls'] for r in rs]}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        keys = sys.argv[2:] or [f"{m}_{c}_{r}" for m in MODES for r in range(1, 4) for c in CONDS]
        with ThreadPoolExecutor(max_workers=3) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
