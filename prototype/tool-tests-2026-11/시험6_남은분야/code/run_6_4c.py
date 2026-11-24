#!/usr/bin/env python3
"""시험 6-4c: ② 출력 줄이기 맞대결 2차 — 도구(MCP)가 큰 결과를 통째로 돌려주는 상황 (rtk vs headroom vs caveman vs 없음)

6-4b(파일 속 한 줄)는 모두 Grep 한 번으로 찾아서 긴 출력이 안 들어옴 → 도구가 일할 상황이 아니었음.
caveman·headroom README 벤치마크처럼 "MCP 도구가 60~90KB를 한 번에 돌려주고, 모델은 그 도구로만 데이터를 볼 수 있는" 상황으로 다시 함.
- 사건 3개는 6-4b와 같은 데이터(log·csv·json, 한 기록만 다름). 데이터 파일은 작업 폴더 밖에 두고 fixture_mcp.py로만 줌.
- 허용 도구: 그 MCP 도구 하나(+TodoWrite). 파일 읽기·검색·셸 없음.
- 조건: none / rtk(셸 명령만 줄이므로 원래 효과 없을 것 — 확인용 1번씩) / headroom(wrap, 압축만) / caveman(wrap, input 모듈)
- 채점: 정답(사건마다 1점), 토큰(전체 / 캐시 읽기 뺀 새 토큰), 시간.
사용법: python run_6_4c.py run [키 ...] | score     키 예: json_caveman_2   (이미 있는 결과는 건너뜀)
"""
import glob
import json
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor

import run_6_4b as b

r64, v1, v3 = b.r64, b.v1, b.v3
HERE = b.HERE
OUT = os.path.join(HERE, "..", "results_6_4c")
CWDS = os.path.join(HERE, "_cwd_6_4c")
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
# 보통 쓰는 것처럼 Read·Grep은 허용(큰 결과가 파일로 빠지면 읽을 수 있게). 데이터는 작업 폴더 밖이라 직접 찾기는 어려움
v1.ALLOWED = "TodoWrite,mcp__fixture,Read,Grep"
v1.DENIED = "PowerShell,WebFetch,WebSearch,Write,Edit,Glob,Bash"
CONDS, CASES = b.CONDS + ["headroomwarm"], b.CASES
# headroomwarm(6-4d) = 미리 켜 둔 headroom 프록시(포트 8899)를 --no-proxy로 다시 씀 → 켜는 시간 빼고 처리 시간만 비교(Codex 제안)
WARM_PORT = 8899
TOOLS = {"log": ("get_service_logs", "결제·주문 서비스의 오늘 로그 전체를 돌려줍니다."),
         "csv": ("get_transactions", "이번 달 카드 거래 내역 전체를 CSV로 돌려줍니다."),
         "json": ("get_deployments", "모든 서비스의 배포 상태를 JSON으로 돌려줍니다.")}
FILES = {"log": "app.log", "csv": "transactions.csv", "json": "deployments.json"}
_cfg = {}


def _run(cmd, **kw):
    cmd = list(cmd)
    c = _cfg.get(kw.get("cwd"))
    if not c or "--settings" not in cmd:
        return b._prev(cmd, **kw)
    settings = json.loads(v3.SETTINGS)
    if c["cond"] == "rtk":
        settings.update(json.loads(r64.HOOK))
    cmd[cmd.index("--settings") + 1] = json.dumps(settings)
    cmd[cmd.index("--setting-sources") + 1] = v3.SOURCES
    cmd += ["--mcp-config", json.dumps({"mcpServers": {"fixture": c["mcp"]}})]
    if c["wrap"]:
        cmd = c["wrap"] + cmd[1:]
    return v3._orig_run(cmd, **kw)


v1.subprocess.run = _run


def run_one(key):
    case, cname, rep = key.split("_")
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    cwd = os.path.join(CWDS, key)
    data = cwd + "_data"
    shutil.rmtree(cwd, ignore_errors=True)
    shutil.rmtree(data, ignore_errors=True)
    os.makedirs(cwd, exist_ok=True)  # 프록시가 폴더를 잡고 있으면 rmtree가 덜 지움
    prompt, answer = b.make_case(case, data, seed=CASES.index(case) * 10 + int(rep), small=True)  # 6-4b와 같은 모양, 크기만 1.5만~2만 토큰
    tool, desc = TOOLS[case]
    q = prompt.replace(FILES[case], f"{tool} 도구로 받은 데이터").replace("파일을 보고", "데이터를 보고")
    wrap = None
    if cname == "headroom":
        wrap = [b.HEADROOM, "wrap", "claude", "--no-mcp", "--code-memory", "none", "--port", str(8810 + CASES.index(case) * 3 + int(rep)), "--"]
    elif cname == "headroomwarm":
        wrap = [b.HEADROOM, "wrap", "claude", "--no-mcp", "--code-memory", "none", "--no-proxy", "--port", str(WARM_PORT), "--"]
    elif cname == "caveman":
        wrap = ["node", b.CAVEMAN, "wrap", "claude"]
    if cname == "rtk":
        open(os.path.join(cwd, "CLAUDE.md"), "w", encoding="utf-8").write(r64.RTK_MD)
    _cfg[cwd] = dict(cond=cname, wrap=wrap, mcp={"command": sys.executable,
                                                 "args": [os.path.join(HERE, "fixture_mcp.py"), tool, desc, os.path.join(data, FILES[case])]})
    t = v1.run_turn(cwd, {}, "사내 시스템 도구를 연결해 뒀어. " + q, key, 1)
    text = t.get("result") or "\n".join(t["texts"][-2:])
    u = v1.tokens(t["usage"])
    rec = dict(case=case, condition=cname, rep=int(rep), data_bytes=os.path.getsize(os.path.join(data, FILES[case])), sec=t["sec"],
               rc=t["rc"], turns=t["turns"], tokens=u["input"] + u["cache_create"] + u["cache_read"] + u["output"],
               new_tokens=u["input"] + u["cache_create"] + u["output"], usage=u, answer=answer, correct=b.check(answer, text),
               denied=t["denied"], stderr=t.get("stderr"), result=text[-1200:])
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: 정답 {rec['correct']}  토큰 {rec['tokens']:,} (새 {rec['new_tokens']:,})  {t['sec']:.0f}초  rc {t['rc']}"


def score():
    tot = {}
    for case in CASES:
        print(f"== {case}")
        for cname in CONDS:
            rs = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(OUT, f"{case}_{cname}_?.json")))]
            for r in rs:
                r["correct"] = b.check(r["answer"], r["result"])  # 채점 규칙을 고치면 저장된 답으로 다시 채점
            if rs:
                n = len(rs)
                tot.setdefault(cname, []).extend(rs)
                print(f"[{cname}] 정답 {sum(r['correct'] for r in rs)}/{n}  평균 토큰 {sum(r['tokens'] for r in rs) // n:,}"
                      f"  새 토큰 {sum(r['new_tokens'] for r in rs) // n:,}  평균 {sum(r['sec'] for r in rs) / n:.0f}초")
    print("== 합계")
    for cname, rs in tot.items():
        n = len(rs)
        print(f"[{cname}] 정답 {sum(r['correct'] for r in rs)}/{n}  평균 토큰 {sum(r['tokens'] for r in rs) // n:,}  새 토큰 {sum(r['new_tokens'] for r in rs) // n:,}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        keys = sys.argv[2:] or ([f"{c}_{n}_{r}" for r in range(1, 4) for c in CASES for n in CONDS if n != "rtk"]
                                + [f"{c}_rtk_1" for c in CASES])
        with ThreadPoolExecutor(max_workers=3) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
