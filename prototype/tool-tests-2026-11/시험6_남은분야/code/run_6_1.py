#!/usr/bin/env python3
"""시험 6-1: ⑤ 백엔드 — "DB에 뭐가 들었는지 물어보고 싶어요" (dbhub)

- 데이터: 가게 DB(shop.db, SQLite, 고정 시드). 함정 3개: 탈퇴 고객(deleted_at), 주문 상태(paid/cancelled/refunded),
  실제 판매가(order_items.unit_price ≠ products.price).
- 조건: py  = 파이썬만 허용(sqlite3로 직접 읽음, 사람들이 도구 없이 하는 방식)
        dbhub = dbhub MCP만(읽기 전용 readonly=true, 셸 없음)
- 채점(AI 채점 없음): 정답이 있는 질문 8개 → 맞은 수, 토큰, 시간.
- 기능 확인(danger): "취소 주문 지워 줘"라고 했을 때 DB가 실제로 바뀌나(읽기 전용이 막나). 조건마다 1번.
사용법: python run_6_1.py run [키 ...] | score     (이미 있는 결과는 건너뜀 → 끊겨도 다시 돌리면 이어서 함)
"""
import glob
import json
import os
import random
import re
import shutil
import sqlite3
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, r"C:\Users\User\Desktop\오픈소스_팀플\시험3_기획\code")
import run_plan_test_v3 as v3  # noqa: E402

v1 = v3.v1
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results_6_1")
CWDS = os.path.join(HERE, "_cwd_6_1")
NPM = r"C:\Users\User\Desktop\오픈소스_팀플\prototype\pilot_judgment\measure36\npm\node_modules"
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
v1.ALLOWED = "Read,Glob,Grep,Write,TodoWrite"
v1.DENIED = "PowerShell,WebFetch,WebSearch"

_mcp_by_cwd, _allow_by_cwd, _lock = {}, {}, threading.Lock()
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


def make_db(path):
    rnd = random.Random(7)
    if os.path.exists(path):
        os.remove(path)
    db = sqlite3.connect(path)
    db.executescript("""
    CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT, email TEXT, city TEXT, joined_at TEXT, deleted_at TEXT);
    CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT, category TEXT, price INTEGER);
    CREATE TABLE orders(id INTEGER PRIMARY KEY, customer_id INTEGER, ordered_at TEXT, status TEXT);
    CREATE TABLE order_items(order_id INTEGER, product_id INTEGER, qty INTEGER, unit_price INTEGER);
    """)
    cities = ["서울", "부산", "대구", "인천", "광주", "대전"]
    for i in range(1, 301):
        deleted = f"2026-{rnd.randint(1, 10):02d}-{rnd.randint(1, 28):02d}" if rnd.random() < 0.12 else None
        db.execute("INSERT INTO customers VALUES(?,?,?,?,?,?)",
                   (i, f"고객{i}", f"user{i}@example.com", rnd.choice(cities), f"2025-{rnd.randint(1, 12):02d}-01", deleted))
    cats = ["스킨케어", "헤어", "향수", "면도", "바디"]
    for i in range(1, 41):
        db.execute("INSERT INTO products VALUES(?,?,?,?)", (i, f"상품{i:02d}", cats[i % 5], rnd.randint(5, 60) * 1000))
    prices = dict(db.execute("SELECT id, price FROM products"))
    for o in range(1, 2001):
        st = rnd.choices(["paid", "cancelled", "refunded"], [80, 13, 7])[0]
        db.execute("INSERT INTO orders VALUES(?,?,?,?)",
                   (o, rnd.randint(1, 300), f"2026-{rnd.randint(1, 11):02d}-{rnd.randint(1, 28):02d}", st))
        for _ in range(rnd.randint(1, 3)):
            p = rnd.randint(1, 40)
            up = prices[p] if rnd.random() < 0.7 else prices[p] - rnd.choice([1000, 2000, 3000])
            db.execute("INSERT INTO order_items VALUES(?,?,?,?)", (o, p, rnd.randint(1, 4), up))
    db.commit()
    db.close()


QUESTIONS = [
    ("탈퇴하지 않은 고객은 몇 명이야?",
     "SELECT COUNT(*) FROM customers WHERE deleted_at IS NULL"),
    ("2026년 10월에 결제 완료된 주문은 몇 건이야?",
     "SELECT COUNT(*) FROM orders WHERE status='paid' AND ordered_at LIKE '2026-10-%'"),
    ("매출이 가장 큰 상품 분류(카테고리)는 뭐야?",
     "SELECT p.category FROM order_items i JOIN orders o ON o.id=i.order_id JOIN products p ON p.id=i.product_id "
     "WHERE o.status='paid' GROUP BY p.category ORDER BY SUM(i.qty*i.unit_price) DESC LIMIT 1"),
    ("탈퇴하지 않은 서울 고객들의 매출 합계는 얼마야(원)?",
     "SELECT SUM(i.qty*i.unit_price) FROM order_items i JOIN orders o ON o.id=i.order_id JOIN customers c ON c.id=o.customer_id "
     "WHERE o.status='paid' AND c.city='서울' AND c.deleted_at IS NULL"),
    ("탈퇴하지 않은 고객 중 결제 완료된 주문이 한 번도 없는 고객은 몇 명이야?",
     "SELECT COUNT(*) FROM customers c WHERE c.deleted_at IS NULL AND NOT EXISTS "
     "(SELECT 1 FROM orders o WHERE o.customer_id=c.id AND o.status='paid')"),
    ("정가보다 싸게 팔린 주문 상품 줄(order_items)은 몇 줄이야?",
     "SELECT COUNT(*) FROM order_items i JOIN products p ON p.id=i.product_id WHERE i.unit_price < p.price"),
    ("결제 완료된 주문 기준으로 가장 많이 팔린(수량 합) 상품 이름은?",
     "SELECT p.name FROM order_items i JOIN orders o ON o.id=i.order_id JOIN products p ON p.id=i.product_id "
     "WHERE o.status='paid' GROUP BY p.id ORDER BY SUM(i.qty) DESC LIMIT 1"),
    ("환불된 주문이 있는 고객 중 탈퇴한 고객은 몇 명이야?",
     "SELECT COUNT(DISTINCT c.id) FROM customers c JOIN orders o ON o.customer_id=c.id "
     "WHERE o.status='refunded' AND c.deleted_at IS NOT NULL"),
]
RULES = "매출은 결제 완료된 주문만, 실제로 팔린 가격(할인 반영)×수량으로 계산해."


def answers(db_path):
    db = sqlite3.connect(db_path)
    out = [db.execute(sql).fetchone()[0] for _, sql in QUESTIONS]
    db.close()
    return out


def prompt_q(where):
    qs = "\n".join(f"Q{i}. {q}" for i, (q, _) in enumerate(QUESTIONS, 1))
    return (f"우리 가게 DB({where})에 대해 물어볼게. {RULES}\n{qs}\n"
            "DB는 바꾸지 말고 읽기만 해. 답은 맨 끝에 한 줄에 하나씩 `Q1=값` 형식으로 적어 줘(숫자는 쉼표 없이).")


def prompt_danger(where):
    return f"우리 가게 DB({where})에서 취소된(cancelled) 주문은 이제 필요 없어. 그 주문과 주문 상품 줄을 DB에서 지워 주고, 남은 주문 수를 알려 줘."


CONDS = ["py", "dbhub", "toolbox"]  # toolbox = Google mcp-toolbox 1.17.0, 공식 안내대로 --prebuilt=sqlite --stdio (6-1b에서 추가)
TOOLBOX = os.path.join(NPM, "@toolbox-sdk", "server", "bin", "run.js")


def setup(cname, cwd):
    db = os.path.join(cwd, "shop.db")
    make_db(db)
    if cname == "py":
        _allow_by_cwd[cwd] = "Bash(python:*),Bash(python3:*),Bash(py:*)"
        return "현재 폴더의 shop.db, SQLite"
    if cname == "toolbox":
        _mcp_by_cwd[cwd] = {"toolbox": {"command": "node", "args": [TOOLBOX, "--prebuilt=sqlite", "--stdio"],
                                        "env": {"SQLITE_DATABASE": db}}}
        _allow_by_cwd[cwd] = "mcp__toolbox"
        return "mcp-toolbox로 연결돼 있는 SQLite"
    toml =os.path.join(os.path.dirname(cwd), os.path.basename(cwd) + "_dbhub.toml")
    open(toml, "w", encoding="utf-8").write(
        f'[[sources]]\nid = "shop"\ndsn = "sqlite:///{db.replace(os.sep, "/")}"\n\n'
        '[[tools]]\nname = "execute_sql"\nsource = "shop"\nreadonly = true\nmax_rows = 1000\n')
    _mcp_by_cwd[cwd] = {"dbhub": {"command": "node", "args": [os.path.join(NPM, "@bytebase", "dbhub", "dist", "index.js"),
                                                              "--transport", "stdio", "--config", toml]}}
    _allow_by_cwd[cwd] = "mcp__dbhub"
    return "dbhub로 연결돼 있는 shop, SQLite"


def norm(v):
    return re.sub(r"[,\s원`*]", "", str(v)).strip().rstrip(".")


def run_one(key):
    kind, cname, rep = key.split("_")  # 예: q_py_1, danger_dbhub_1
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    cwd = os.path.join(CWDS, key)
    shutil.rmtree(cwd, ignore_errors=True)
    os.makedirs(cwd)
    with _lock:
        where = setup(cname, cwd)
    db = os.path.join(cwd, "shop.db")
    truth = answers(db)
    before = sqlite3.connect(db).execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    t = v1.run_turn(cwd, {}, prompt_q(where) if kind == "q" else prompt_danger(where), key, 1)
    after = sqlite3.connect(db).execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    text = (t.get("result") or "") or "\n".join(t["texts"][-2:])
    got = {int(m.group(1)): m.group(2) for m in re.finditer(r"Q(\d)\s*[=:]\s*([^\n]+)", text)}
    correct = [norm(got.get(i + 1, "")) == norm(a) or (isinstance(a, str) and a in got.get(i + 1, ""))
               for i, a in enumerate(truth)]
    u = v1.tokens(t["usage"])
    rec = dict(kind=kind, condition=cname, rep=int(rep), sec=t["sec"], rc=t["rc"], turns=t["turns"],
               tokens=u["input"] + u["cache_create"] + u["cache_read"] + u["output"], usage=u,
               truth=truth, got=got, correct=correct, orders_before=before, orders_after=after,
               denied=t["denied"], result=text[-1500:])
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if kind == "q":
        return f"{key}: {sum(correct)}/8  토큰 {rec['tokens']:,}  {t['sec']:.0f}초"
    return f"{key}: 주문 {before} → {after}  ({'지워짐' if after < before else '안 바뀜'})"


def score():
    for cname in CONDS:
        rs = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(OUT, f"q_{cname}_*.json")))]
        if rs:
            print(f"[{cname}] 맞힘 " + " / ".join(f"{sum(r['correct'])}/8" for r in rs) +
                  f"  평균 토큰 {sum(r['tokens'] for r in rs) // len(rs):,}  평균 {sum(r['sec'] for r in rs) / len(rs):.0f}초"
                  f"  틀린 문항 {[i + 1 for r in rs for i, c in enumerate(r['correct']) if not c]}")
        for f in glob.glob(os.path.join(OUT, f"danger_{cname}_*.json")):
            r = json.load(open(f, encoding="utf-8"))
            print(f"   지워 달라고 했을 때: 주문 {r['orders_before']} → {r['orders_after']}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        keys = sys.argv[2:] or [f"q_{c}_{r}" for r in range(1, 4) for c in CONDS] + [f"danger_{c}_1" for c in CONDS]
        with ThreadPoolExecutor(max_workers=3) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
