#!/usr/bin/env python3
"""시험 6-4b: ② 출력 줄이기 맞대결 — rtk vs headroom vs caveman vs 없음
도구들이 강하다는 상황: 아주 긴 로그·CSV·JSON 안에 중요한 한 줄이 묻혀 있을 때(caveman·headroom README의 벤치마크와 같은 모양).

- 사건 3개(각 60~90KB, 기록 하나만 다름, 정답 정확히 채점):
  log  = 서비스 로그 1,600줄 중 결제 실패 ERROR 한 줄 → 거래 번호·오류 이름
  csv  = 거래 1,500줄 중 금액이 혼자 튀는 거래 한 줄 → 거래 id·금액
  json = 서비스 420개 배포 상태 중 실행 개수가 원하는 개수와 다른 하나 → 서비스 이름·실행 개수
- 조건: none / rtk(Bash 훅, 6-4와 같음) / headroom(`headroom wrap claude --no-mcp --code-memory none`, 압축만)
        / caveman(`caveman wrap claude`, 기본 압축)
  headroom·caveman은 내 컴퓨터에 프록시를 띄워 Claude 요청을 거쳐 보냄(압축은 로컬). 통계 보내기 끔.
- 채점(AI 채점 없음): 정답(사건마다 1점), 토큰(입력+캐시+출력), 시간.
사용법: python run_6_4b.py run [키 ...] | score     키 예: log_caveman_1   (이미 있는 결과는 건너뜀)
"""
import glob
import json
import os
import random
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor

import run_6_4 as r64  # rtk 훅(v3 설정과 합치는 방식 포함)을 그대로 씀

v1, v3 = r64.v1, r64.v3
HERE = r64.HERE
OUT = os.path.join(HERE, "..", "results_6_4b")
CWDS = os.path.join(HERE, "_cwd_6_4b")
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
v1.ALLOWED = ("Read,Glob,Grep,TodoWrite,Bash(python:*),Bash(cat:*),Bash(head:*),Bash(tail:*),Bash(wc:*),Bash(grep:*),"
              "Bash(rtk:*),Bash(ls:*)")
v1.DENIED = "PowerShell,WebFetch,WebSearch,Write,Edit"
HEADROOM = r"C:\Users\User\tools\headroom-venv\Scripts\headroom.exe"
CAVEMAN = r"C:\Users\User\Desktop\오픈소스_팀플\prototype\pilot_judgment\measure36\npm\node_modules\@caveman-ai\cli\dist\index.js"
os.environ.update(HEADROOM_TELEMETRY="off", HEADROOM_BEACON="off", DO_NOT_TRACK="1")
os.environ["PATH"] = os.path.dirname(v1.CLAUDE) + os.pathsep + os.environ["PATH"]  # 래퍼가 claude를 PATH에서 찾음
CONDS = ["none", "rtk", "headroom", "caveman"]
CASES = ["log", "csv", "json"]
_wrap_by_cwd = {}
_prev = v1.subprocess.run


def _run(cmd, **kw):
    cmd = list(cmd)
    w = _wrap_by_cwd.get(kw.get("cwd"))
    if w and "--settings" in cmd:
        # v3 설정(사용자 CLAUDE.md 빼기 등)을 직접 적용하고, claude 대신 "래퍼 wrap claude ..."로 실행
        cmd[cmd.index("--settings") + 1] = v3.SETTINGS
        cmd[cmd.index("--setting-sources") + 1] = v3.SOURCES
        return v3._orig_run(w + cmd[1:], **kw)
    return _prev(cmd, **kw)


v1.subprocess.run = _run


def make_case(case, dst, seed, small=False):
    # small=True: 6-4c용(1.5만~2만 토큰). Claude Code는 2.5만 토큰 넘는 도구 결과를 파일로 빼 두기 때문
    rnd = random.Random(seed)
    k = 0.5 if small else 1.0
    os.makedirs(dst, exist_ok=True)
    if case == "log":
        svcs = ["auth", "cart", "search", "inventory", "payment", "notify"]
        lines = []
        for i in range(int(1600 * k)):
            s = rnd.choice(svcs)
            lvl = rnd.choices(["INFO", "DEBUG", "WARN"], [70, 22, 8])[0]
            msg = {"INFO": f"request ok path=/api/{s}/{rnd.randint(1, 999)} ms={rnd.randint(3, 240)}",
                   "DEBUG": f"cache hit key={s}:{rnd.randint(1000, 9999)} ttl={rnd.randint(10, 600)}",
                   "WARN": f"slow upstream retry={rnd.randint(1, 3)} txn=TX-{rnd.randint(10000, 99999)}"}[lvl]
            lines.append(f"2026-11-19T{9 + i // 200:02d}:{(i * 7) % 60:02d}:{(i * 13) % 60:02d}Z {lvl:5} [{s}] {msg}")
        txn = f"TX-{rnd.randint(10000, 99999)}"
        pos = rnd.randint(int(700 * k), int(900 * k))
        lines[pos] = lines[pos][:21] + f"ERROR [payment] charge failed txn={txn} err=GatewayTimeoutError upstream=pg-kr-2"
        open(os.path.join(dst, "app.log"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
        return ("app.log 파일을 보고, 결제가 실패한 거래가 있으면 그 거래 번호와 오류 이름을 알려 줘.",
                {"txn": txn, "err": "GatewayTimeoutError"})
    if case == "csv":
        rows = ["id,date,store,category,amount,card_last4"]
        for i in range(int(1500 * k * 1.3)):
            rows.append(f"T{100000 + i},2026-11-{rnd.randint(1, 18):02d},S{rnd.randint(1, 40):02d},"
                        f"{rnd.choice(['food', 'beauty', 'book', 'cafe', 'grocery'])},{rnd.randint(3, 90) * 100},{rnd.randint(1000, 9999)}")
        pos = rnd.randint(int(600 * k), int(900 * k))
        parts = rows[pos].split(",")
        parts[4] = str(rnd.randint(180, 260) * 10000)
        rows[pos] = ",".join(parts)
        open(os.path.join(dst, "transactions.csv"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
        return ("transactions.csv에 금액이 혼자 터무니없이 큰 이상 거래가 하나 있어. 그 거래의 id와 금액을 알려 줘.",
                {"id": parts[0], "amount": parts[4]})
    svcs = []
    for i in range(int(420 * k * 1.4)):
        n = rnd.randint(1, 6)
        svcs.append({"name": f"svc-{rnd.choice(['api', 'web', 'worker', 'cron', 'db'])}-{i:03d}", "image": f"repo/app:{rnd.randint(1, 90)}",
                     "replicas": {"desired": n, "running": n}, "region": rnd.choice(["kr-1", "kr-2", "jp-1"]),
                     "labels": {"team": rnd.choice(["a", "b", "c", "d"]), "tier": rnd.choice(["gold", "silver"])}})
    pos = rnd.randint(int(150 * k), int(300 * k))
    svcs[pos]["replicas"]["running"] = max(0, svcs[pos]["replicas"]["desired"] - rnd.randint(1, 3))
    open(os.path.join(dst, "deployments.json"), "w", encoding="utf-8").write(json.dumps({"services": svcs}, indent=None if small else 2))
    return ("deployments.json에서 실행 중인 개수(running)가 원하는 개수(desired)와 다른 서비스가 하나 있어. 그 서비스 이름과 실행 개수를 알려 줘.",
            {"name": svcs[pos]["name"], "running": str(svcs[pos]["replicas"]["running"])})


def check(answer, text):
    t = text.replace(",", "")
    # 앞뒤가 영문·숫자·하이픈이 아니면 맞음("2,200,000원"처럼 한글이 바로 붙어도 정답으로 봄 — 처음엔 \w라서 한글 때문에 오답 처리됐음)
    return all(re.search(r"(?<![0-9A-Za-z-])" + re.escape(v) + r"(?![0-9A-Za-z-])", t) for v in answer.values())


def run_one(key):
    case, cname, rep = key.split("_")
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    cwd = os.path.join(CWDS, key)
    shutil.rmtree(cwd, ignore_errors=True)
    prompt, answer = make_case(case, cwd, seed=CASES.index(case) * 10 + int(rep))
    size = sum(os.path.getsize(os.path.join(cwd, f)) for f in os.listdir(cwd))
    if cname == "rtk":
        open(os.path.join(cwd, "CLAUDE.md"), "w", encoding="utf-8").write(r64.RTK_MD)
        r64._settings_by_cwd[cwd] = r64.HOOK
    elif cname == "headroom":
        port = 8790 + CASES.index(case) * 3 + int(rep)
        _wrap_by_cwd[cwd] = [HEADROOM, "wrap", "claude", "--no-mcp", "--code-memory", "none", "--port", str(port), "--"]
    elif cname == "caveman":
        _wrap_by_cwd[cwd] = ["node", CAVEMAN, "wrap", "claude"]
    t = v1.run_turn(cwd, {}, prompt + " 파일은 고치지 마.", key, 1)
    text = t.get("result") or "\n".join(t["texts"][-2:])
    u = v1.tokens(t["usage"])
    rec = dict(case=case, condition=cname, rep=int(rep), file_bytes=size, sec=t["sec"], rc=t["rc"], turns=t["turns"],
               tokens=u["input"] + u["cache_create"] + u["cache_read"] + u["output"], usage=u, answer=answer,
               correct=check(answer, text), stderr=t.get("stderr"), result=text[-1200:])
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: 정답 {rec['correct']}  토큰 {rec['tokens']:,}  {t['sec']:.0f}초  rc {t['rc']}"


def score():
    for case in CASES:
        print(f"== {case}")
        for cname in CONDS:
            rs = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(OUT, f"{case}_{cname}_?.json")))]
            if rs:
                n = len(rs)
                print(f"[{cname}] 정답 {sum(r['correct'] for r in rs)}/{n}  평균 토큰 {sum(r['tokens'] for r in rs) // n:,}"
                      f"  평균 {sum(r['sec'] for r in rs) / n:.0f}초  토큰 {[r['tokens'] for r in rs]}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        keys = sys.argv[2:] or [f"{c}_{n}_{r}" for r in range(1, 4) for c in CASES for n in CONDS]
        with ThreadPoolExecutor(max_workers=3) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
