#!/usr/bin/env python3
"""시험 6-4: ② 토큰 — "긴 출력(로그·테스트) 때문에 토큰이 빨리 줄어요" (rtk 1.2.1)

- 과제: 파이썬 프로젝트(테스트 411개, 그중 5개 실패 — 버그 3개(하나는 사람식 반올림)). 실패한 테스트마다 로그가 수백 줄 찍혀서 출력이 김.
  "테스트 돌려서 실패를 고쳐 줘"라고만 시킴.
- 조건: none = 도구 없음 / rtk = rtk 설치 방식 그대로(rtk init -g가 넣는 Bash 훅 `rtk hook claude` + RTK.md 안내문)
        단, 실제 ~/.claude 설정은 건드리지 않고 시험할 때만 --settings로 훅을 넣음.
- 채점(AI 채점 없음): 끝난 뒤 전체 테스트 통과 여부, 테스트 파일을 고쳤는지(고치면 반칙), 토큰·시간·명령 횟수·도구 출력 글자 수.
사용법: python run_6_4.py run [키 ...] | score     (이미 있는 결과는 건너뜀)
"""
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, r"C:\Users\User\Desktop\오픈소스_팀플\시험3_기획\code")
import run_plan_test_v3 as v3  # noqa: E402

v1 = v3.v1
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results_6_4")
CWDS = os.path.join(HERE, "_cwd_6_4")
RTK = r"C:\Users\User\tools\rtk\rtk.exe"
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
v1.ALLOWED = ("Read,Glob,Grep,Write,Edit,TodoWrite,Bash(python:*),Bash(python -m pytest:*),Bash(pytest:*),"
              "Bash(rtk:*),Bash(ls:*),Bash(cat:*)")
v1.DENIED = "PowerShell,WebFetch,WebSearch"
os.environ["PATH"] = os.path.dirname(RTK) + os.pathsep + os.environ["PATH"]
RTK_MD = """# Command output

Command output here is condensed to save tokens, keeping every signal and
dropping costly noise. Treat it as the complete result: run commands
normally, and batch related commands into one call to avoid extra turns.
Truncated results state their recovery path in their own output. Re-run a
command as `rtk bypass <cmd>` only when its result is unusable: empty when
output was clearly expected, contradicting its exit code, or garbled.
"""
HOOK_LOG = os.path.join(HERE, "..", "results_6_4", "_hook").replace(os.sep, "/")
os.makedirs(HOOK_LOG, exist_ok=True)
# 훅이 실제로 명령을 바꿨는지 보려고 입력·출력을 기록만 함(rtk 동작은 그대로)
HOOK = json.dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command",
        "command": f'tee -a "{HOOK_LOG}/in.jsonl" | rtk hook claude | tee -a "{HOOK_LOG}/out.jsonl"'}]}]}})
CONDS = ["none", "rtk"]
_prev = v1.subprocess.run
_settings_by_cwd = {}


def _run(cmd, **kw):
    # v3 래퍼가 --settings를 자기 값으로 덮어써서 훅이 빠졌음(1차 rtk_1 무효) → v3 설정에 훅을 합쳐서 v3를 건너뛰고 바로 실행
    cmd = list(cmd)
    s = _settings_by_cwd.get(kw.get("cwd"))
    if s and "--settings" in cmd:
        merged = dict(json.loads(v3.SETTINGS), **json.loads(s))
        cmd[cmd.index("--settings") + 1] = json.dumps(merged)
        cmd[cmd.index("--setting-sources") + 1] = v3.SOURCES
        return v3._orig_run(cmd, **kw)
    return _prev(cmd, **kw)


v1.subprocess.run = _run

APP = '''"""작은 재고 관리 모듈."""
import logging

log = logging.getLogger("inventory")


def parse_qty(text):
    log.info("parse_qty input=%r", text)
    text = text.strip()
    if not text.isdigit():
        raise ValueError(f"수량이 숫자가 아님: {text!r}")
    return int(text)


def price_with_tax(price, rate=0.1):
    for step in range(120):
        log.debug("tax step %d price=%s rate=%s", step, price, rate)
    return int(price * (1 + rate))


def merge_stock(a, b):
    out = dict(a)
    for k, v in b.items():
        log.info("merge %s: %s + %s", k, out.get(k), v)
        out[k] = v
    return out


def low_stock(stock, limit=5):
    for k, v in stock.items():
        log.warning("check %s=%s limit=%s", k, v, limit)
    return sorted(k for k, v in stock.items() if v < limit)
'''

TESTS = '''import logging
import pytest
from app import parse_qty, price_with_tax, merge_stock, low_stock

logging.basicConfig(level=logging.DEBUG)


@pytest.mark.parametrize("n", range(400))
def test_parse_many(n):
    assert parse_qty(f" {n} ") == n


@pytest.mark.parametrize("bad", ["", "x", "1.5", "-3"])
def test_parse_bad(bad):
    with pytest.raises(ValueError):
        parse_qty(bad)


@pytest.mark.parametrize("p,want", [(1000, 1100), (999, 1099), (15, 17), (0, 0), (105, 116)])
def test_tax(p, want):
    """세금 포함 가격은 반올림한다."""
    assert price_with_tax(p) == want


def test_merge():
    """같은 상품은 재고를 더한다."""
    big = {f"item{i}": i for i in range(150)}
    assert merge_stock(big, {"item1": 2, "new": 3}) == {**big, "item1": 3, "new": 3}


def test_low():
    """재고가 limit 이하면 부족."""
    stock = {f"s{i}": i for i in range(200)}
    assert low_stock(stock) == sorted(f"s{i}" for i in range(6))
'''


def make_fixture(dst):
    os.makedirs(dst)
    open(os.path.join(dst, "app.py"), "w", encoding="utf-8").write(APP)
    os.makedirs(os.path.join(dst, "tests"))
    open(os.path.join(dst, "tests", "test_app.py"), "w", encoding="utf-8").write(TESTS)
    open(os.path.join(dst, "pytest.ini"), "w", encoding="utf-8").write("[pytest]\npythonpath = .\nlog_level = DEBUG\n")


def tests_hash(cwd):
    return hashlib.md5(open(os.path.join(cwd, "tests", "test_app.py"), "rb").read()).hexdigest()


def pytest_run(cwd):
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    return r.returncode, r.stdout


def run_one(key):
    cname, rep = key.rsplit("_", 1)
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    cwd = os.path.join(CWDS, key)
    shutil.rmtree(cwd, ignore_errors=True)
    make_fixture(cwd)
    h0 = tests_hash(cwd)
    rc0, out0 = pytest_run(cwd)
    if cname == "rtk":
        open(os.path.join(cwd, "CLAUDE.md"), "w", encoding="utf-8").write(RTK_MD)
        _settings_by_cwd[cwd] = HOOK
    t = v1.run_turn(cwd, {}, "테스트를 돌려서 실패하는 걸 고쳐 줘. 테스트 파일은 고치지 말고 app.py만 고쳐.", key, 1)
    rc, outp = pytest_run(cwd)
    jl = os.path.join(OUT, f"{key}_t1.jsonl")
    cmds, tool_out_chars = [], 0
    for line in open(jl, encoding="utf-8", errors="replace"):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if not isinstance(e, dict):
            continue
        msg = e.get("message") or {}
        if not isinstance(msg, dict):
            continue
        content = [c for c in msg.get("content") if isinstance(c, dict)] if isinstance(msg.get("content"), list) else []
        if e.get("type") == "assistant":
            for c in content:
                if c.get("type") == "tool_use" and c.get("name") == "Bash":
                    cmds.append((c.get("input") or {}).get("command", "")[:200])
        elif e.get("type") == "user":
            for c in content:
                if c.get("type") == "tool_result":
                    cc = c.get("content")
                    tool_out_chars += len(cc if isinstance(cc, str) else json.dumps(cc, ensure_ascii=False))
    u = v1.tokens(t["usage"])
    rec = dict(condition=cname, rep=int(rep), sec=t["sec"], rc=t["rc"], turns=t["turns"],
               tokens=u["input"] + u["cache_create"] + u["cache_read"] + u["output"], usage=u,
               start_failed=rc0 != 0, start_output_chars=len(out0), passed=rc == 0, tests_untouched=tests_hash(cwd) == h0,
               bash=cmds, tool_output_chars=tool_out_chars, tail=outp[-300:], result=(t.get("result") or "")[-600:])
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return (f"{key}: 통과 {rec['passed']}  테스트 안 건드림 {rec['tests_untouched']}  토큰 {rec['tokens']:,}  "
            f"도구 출력 {tool_out_chars:,}자  {t['sec']:.0f}초  명령 {len(cmds)}개")


def score():
    for cname in CONDS:
        rs = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(OUT, f"{cname}_?.json")))]
        if rs:
            n = len(rs)
            print(f"[{cname}] 통과 {sum(r['passed'] and r['tests_untouched'] for r in rs)}/{n}  평균 토큰 {sum(r['tokens'] for r in rs) // n:,}"
                  f"  평균 도구 출력 {sum(r['tool_output_chars'] for r in rs) // n:,}자  평균 {sum(r['sec'] for r in rs) / n:.0f}초"
                  f"  명령 수 {[len(r['bash']) for r in rs]}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        keys = sys.argv[2:] or [f"{c}_{r}" for r in range(1, 4) for c in CONDS]
        with ThreadPoolExecutor(max_workers=3) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
