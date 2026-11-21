#!/usr/bin/env python3
"""시험 6-2b: ③ 라이브러리 문서 — context7이 강하다는 상황(모델이 잘 모를 새·덜 알려진 라이브러리)

6-2(Jackson 3)는 모델이 이미 알아서 context7을 안 불렀음 → 애매. 이번엔 덜 알려진 최신 도구 dbhub 2.0의 설정 파일(dbhub.toml).
함정(문서를 봐야 앎): SQLite 사용자 정의 도구는 `?` 자리표시자만 됨($1은 시작부터 실패), 읽기 전용·최대 행 수는 [[tools]]에 씀.
- 과제: dbhub.toml 쓰기 — shop.db를 'shop'으로 연결, execute_sql 읽기 전용·최대 50행, 사용자 정의 도구 count_orders_by_status(status).
  dbhub를 실행해 볼 수 없게 함(한 번에 맞게 써야 함 = 문서가 중요한 상황).
- 조건: none / c7(context7 MCP)
- 채점(AI 채점 없음, 실제로 dbhub를 그 설정으로 띄워서 확인) 4점:
  ① 서버가 뜨고 두 도구가 보임 ② count_orders_by_status(paid) = 1620 ③ DELETE가 막힘 ④ SELECT가 50행 이하
사용법: python run_6_2b.py run [키 ...] | score     (이미 있는 결과는 건너뜀)
"""
import glob
import json
import os
import shutil
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor

import mcp_client
import run_6_1 as r61  # 같은 가게 DB 만들기

sys.path.insert(0, r"C:\Users\User\Desktop\오픈소스_팀플\시험3_기획\code")
import run_plan_test_v3 as v3  # noqa: E402

v1 = v3.v1
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results_6_2b")
CWDS = os.path.join(HERE, "_cwd_6_2b")
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
v1.ALLOWED = "Read,Glob,Grep,Write,Edit,TodoWrite"
v1.DENIED = "PowerShell,WebFetch,WebSearch,Bash"
DBHUB = os.path.join(r61.NPM, "@bytebase", "dbhub", "dist", "index.js")
C7 = os.path.join(r61.NPM, "@upstash", "context7-mcp", "dist", "index.js")
CONDS = ["none", "c7"]
PROMPT = ("dbhub(Bytebase가 만든 DB용 MCP 서버, 2.x 버전)의 설정 파일 dbhub.toml을 이 폴더에 만들어 줘. "
          "이 폴더의 shop.db(SQLite)를 'shop'이라는 이름의 소스로 연결하고, execute_sql 도구는 읽기 전용으로 한 번에 최대 50행만 돌려주게 해. "
          "그리고 주문 상태(paid, cancelled, refunded 중 하나)를 받아서 그 상태인 주문(orders 표의 status 칸) 수를 돌려주는 "
          "사용자 정의 도구 count_orders_by_status를 만들어 줘. 지금은 dbhub를 실행해 볼 수 없으니 한 번에 맞게 써 줘.")
_mcp_by_cwd, _allow_by_cwd = {}, {}
_prev = v1.subprocess.run


def _run(cmd, **kw):
    cmd = list(cmd)
    cfg = _mcp_by_cwd.get(kw.get("cwd"))
    if "--strict-mcp-config" in cmd and cfg:
        cmd += ["--mcp-config", json.dumps({"mcpServers": cfg})]
    extra = _allow_by_cwd.get(kw.get("cwd"))
    if extra and "--allowedTools" in cmd:
        cmd[cmd.index("--allowedTools") + 1] += "," + extra
    return _prev(cmd, **kw)


v1.subprocess.run = _run


def grade(cwd):
    g = dict(starts=False, custom=False, readonly=False, max_rows=False, error=None)
    toml = os.path.join(cwd, "dbhub.toml")
    if not os.path.exists(toml):
        g["error"] = "dbhub.toml 없음"
        g["score"] = 0
        return g
    db = os.path.join(cwd, "shop.db")
    before = sqlite3.connect(db).execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    c = None
    try:
        c = mcp_client.Client(["node", DBHUB, "--transport", "stdio", "--config", toml], cwd=cwd)
        names = [t["name"] for t in c.call("tools/list")["result"]["tools"]]
        g["tools"] = names
        sql_tool = next((n for n in names if n.startswith("execute_sql")), None)
        g["starts"] = bool(sql_tool) and "count_orders_by_status" in names
        if "count_orders_by_status" in names:
            r = c.call("tools/call", {"name": "count_orders_by_status", "arguments": {"status": "paid"}})
            g["custom"] = "1620" in json.dumps(r)
        if sql_tool:
            c.call("tools/call", {"name": sql_tool, "arguments": {"sql": "DELETE FROM orders WHERE status='cancelled'"}})
            g["readonly"] = sqlite3.connect(db).execute("SELECT COUNT(*) FROM orders").fetchone()[0] == before
            r = c.call("tools/call", {"name": sql_tool, "arguments": {"sql": "SELECT id FROM orders"}})
            txt = r.get("result", {}).get("content", [{}])[0].get("text", "")
            try:
                rows = json.loads(txt)["data"]["statements"][0]["rows"]
                g["max_rows"] = len(rows) <= 50
                g["rows"] = len(rows)
            except Exception:
                g["max_rows"] = False
    except Exception as e:
        g["error"] = str(e)[-400:]
    finally:
        if c:
            c.close()
    g["score"] = sum(g[k] for k in ("starts", "custom", "readonly", "max_rows"))
    return g


def run_one(key):
    cname, rep = key.rsplit("_", 1)
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    cwd = os.path.join(CWDS, key)
    shutil.rmtree(cwd, ignore_errors=True)
    os.makedirs(cwd, exist_ok=True)
    r61.make_db(os.path.join(cwd, "shop.db"))
    if cname == "c7":
        _mcp_by_cwd[cwd] = {"context7": {"command": "node", "args": [C7]}}
        _allow_by_cwd[cwd] = "mcp__context7"
    t = v1.run_turn(cwd, {}, PROMPT, key, 1)
    g = grade(cwd)
    jl = os.path.join(OUT, f"{key}_t1.jsonl")
    c7 = sum(1 for line in open(jl, encoding="utf-8", errors="replace") if '"name":"mcp__context7' in line and '"tool_use"' in line)
    u = v1.tokens(t["usage"])
    toml = os.path.join(cwd, "dbhub.toml")
    rec = dict(condition=cname, rep=int(rep), sec=t["sec"], rc=t["rc"], turns=t["turns"],
               tokens=u["input"] + u["cache_create"] + u["cache_read"] + u["output"], usage=u, grade=g, c7_calls=c7,
               toml=open(toml, encoding="utf-8").read()[:3000] if os.path.exists(toml) else None, result=(t.get("result") or "")[-800:])
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: {g['score']}/4  {g.get('error') or ''}  토큰 {rec['tokens']:,}  {t['sec']:.0f}초  context7 {c7}번"


def score():
    for cname in CONDS:
        rs = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(OUT, f"{cname}_?.json")))]
        if rs:
            n = len(rs)
            print(f"[{cname}] 점수 {[r['grade']['score'] for r in rs]}  평균 토큰 {sum(r['tokens'] for r in rs) // n:,}"
                  f"  평균 {sum(r['sec'] for r in rs) / n:.0f}초  context7 {[r['c7_calls'] for r in rs]}"
                  f"  실패 {[(r['grade'].get('error') or '')[:60] for r in rs]}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        keys = sys.argv[2:] or [f"{c}_{r}" for r in range(1, 4) for c in CONDS]
        with ThreadPoolExecutor(max_workers=3) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
