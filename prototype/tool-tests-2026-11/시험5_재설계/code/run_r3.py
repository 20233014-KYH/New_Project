#!/usr/bin/env python3
"""R3: 브라우저 도구가 맡는 상황 — "코드 없는 배포 사이트의 E2E 테스트 만들기".

- 사이트: fixture_r3 (할 일 추가·완료·삭제·필터). 작업 폴더에는 코드를 주지 않는다(배포 상황).
- 조건: curl 그 사이트에만 curl 허용(브라우저 도구 없이 HTML·JS를 받아 읽고 작성) / pw playwright-mcp / cdt chrome-devtools-mcp
  셋 다 만든 테스트를 `npx playwright test`로 돌려 볼 수 있다(같은 조건).
- 채점(AI 채점 없음): 만든 테스트를 정상 사이트에 2번(둘 다 통과해야 함) + 고장 사이트 4개(추가·완료 개수·삭제·필터)에 돌려
  고장을 몇 개 잡는지(테스트가 실패하면 잡은 것). 정상 사이트에서 실패하면 0점(지어낸 선택자 등).
사용법: python run_r3.py run [키 ...] | score
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, r"C:\Users\User\Desktop\오픈소스_팀플\시험3_기획\code")
import run_plan_test_v3 as v3  # noqa: E402

v1 = v3.v1
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results_r3")
CWDS = os.path.join(HERE, "_cwd_r3")  # 여기에 @playwright/test 설치(node_modules) → 아래 폴더들에서 찾아 씀
SITE = os.path.join(HERE, "fixture_r3")
NPM = r"C:\Users\User\Desktop\오픈소스_팀플\prototype\pilot_judgment\measure36\npm\node_modules"
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
v1.ALLOWED = "Read,Glob,Grep,Write,Edit,TodoWrite,mcp__playwright,mcp__chrome-devtools,Bash(npx playwright test*)"
v1.DENIED = "PowerShell,WebFetch,WebSearch"

MCP = {
    "pw": {"playwright": {"command": "node", "args": [os.path.join(NPM, "@playwright", "mcp", "cli.js"), "--headless", "--isolated"]}},
    "cdt": {"chrome-devtools": {"command": "node", "args": [os.path.join(NPM, "chrome-devtools-mcp", "build", "src", "bin", "chrome-devtools-mcp.js"), "--headless", "--isolated"]}},
}
CONDS = ["curl", "pw", "cdt"]
PORT_BASE, GRADE_BASE = 8900, 9100  # R3b는 다른 값으로 바꿔 씀
MUTANTS = {
    "추가(글자 잘림)": ("/*TEXT*/t.x", "t.x.slice(0,-1)"),
    "완료 개수": ('/*LEFT*/"남은 할 일 "+k+"개"', '"남은 할 일 "+s.length+"개"'),
    "삭제(엉뚱한 항목)": ("/*DELETE*/s=s.filter(", "s=s.slice(1);r();return;s=s.filter("),
    "필터": ("/*FILTER*/return", "return true;return"),
}

_mcp_by_cwd, _allow_by_cwd, _lock = {}, {}, threading.Lock()
_prev = v1.subprocess.run


def _run(cmd, **kw):
    cmd = list(cmd)
    if "--max-turns" in cmd:
        cmd[cmd.index("--max-turns") + 1] = "80"
    cfg = _mcp_by_cwd.get(kw.get("cwd"))
    if "--strict-mcp-config" in cmd and cfg:
        cmd += ["--mcp-config", json.dumps({"mcpServers": cfg})]
    extra = _allow_by_cwd.get(kw.get("cwd"))
    if extra and "--allowedTools" in cmd:
        i = cmd.index("--allowedTools") + 1
        cmd[i] += "," + extra
    return _prev(cmd, **kw)


v1.subprocess.run = _run


def make_site(dst, mutant=None):
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(SITE, dst)
    if mutant:
        a, b = MUTANTS[mutant]
        p = os.path.join(dst, "app.js")
        src = open(p, encoding="utf-8").read()
        assert a in src, mutant
        open(p, "w", encoding="utf-8").write(src.replace(a, b))


def serve(folder, port):
    return subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=folder,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run_one(key):
    cname, rep = key.rsplit("_r", 1)
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    idx = CONDS.index(cname) * 3 + int(rep)
    port = PORT_BASE + idx
    cwd = os.path.join(CWDS, key)
    site = os.path.join(CWDS, f"{key}_site")
    shutil.rmtree(cwd, ignore_errors=True)
    os.makedirs(cwd)
    make_site(site)
    srv = serve(site, port)
    try:
        with _lock:
            _mcp_by_cwd[cwd] = MCP.get(cname)
            if cname == "curl":
                _allow_by_cwd[cwd] = f"Bash(curl *127.0.0.1:{port}*)"
        url = f"http://127.0.0.1:{port}/"
        prompt = (f"배포된 할 일 사이트 {url} 의 Playwright E2E 테스트를 tests/todo.spec.js 파일로 만들어 줘. 사이트 코드는 나한테 없어. "
                  "할 일 추가, 완료 체크(남은 개수 표시 포함), 삭제, 보기 필터(전체/진행 중/완료)가 제대로 되는지 확인해야 해. "
                  f"주소는 process.env.BASE_URL로 받고, 없으면 {url} 를 써. "
                  "@playwright/test는 이미 설치돼 있고 `npx playwright test`로 돌려 볼 수 있어. 다 되면 테스트가 무엇을 확인하는지 짧게 알려 줘.")
        t = v1.run_turn(cwd, {}, prompt, key, 1)
    finally:
        srv.terminate()
    u = v1.tokens(t["usage"])
    grade = grade_tests(key, cwd, port, idx)
    rec = dict(condition=cname, rep=int(rep), turn=t, grade=grade,
               tokens=dict(total_in=u["input"] + u["cache_create"] + u["cache_read"], output=u["output"]))
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: 끝 ({t['sec']}초, rc={t['rc']}, 정상통과={grade.get('orig')}, 잡은 고장={grade.get('killed')})"


def grade_tests(key, cwd, own_port, idx):
    specs = [p for p in glob.glob(os.path.join(cwd, "**", "*.spec.*"), recursive=True) if "node_modules" not in p]
    if not specs:
        return dict(orig=None, killed=0, note="테스트 파일 없음")
    keep = os.path.join(OUT, f"{key}_tests")
    shutil.rmtree(keep, ignore_errors=True)
    shutil.copytree(cwd, keep, ignore=shutil.ignore_patterns("node_modules", "test-results", "playwright-report", ".claude"))
    res = {}
    variants = [("정상1", None), ("정상2", None)] + [(m, m) for m in MUTANTS]
    for j, (name, mut) in enumerate(variants):
        port = GRADE_BASE + idx * 10 + j
        site = os.path.join(CWDS, f"{key}_g{j}_site")
        work = os.path.join(CWDS, f"{key}_g{j}")
        make_site(site, mut)
        shutil.rmtree(work, ignore_errors=True)
        shutil.copytree(keep, work)
        url = f"http://127.0.0.1:{port}/"
        # 테스트·설정 파일에 박힌 원래 주소도 바꾼다(BASE_URL을 안 쓴 경우 대비)
        for p in glob.glob(os.path.join(work, "**", "*.*"), recursive=True):
            if p.endswith((".js", ".ts", ".mjs", ".cjs")):
                s = open(p, encoding="utf-8", errors="replace").read()
                s2 = re.sub(rf"http://(127\.0\.0\.1|localhost):{own_port}/?", url, s)
                if s2 != s:
                    open(p, "w", encoding="utf-8").write(s2)
        srv = serve(site, port)
        try:
            env = dict(os.environ, BASE_URL=url, CI="1")
            # 목록으로 넘긴다: 시험 3 장치의 subprocess.run 감싸기가 문자열 명령을 글자 단위로 쪼개 버림(처음에 그래서 전부 실패로 나옴)
            p = subprocess.run([shutil.which("npx"), "playwright", "test", "--reporter=line", "--workers=1"], cwd=work, env=env,
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
            res[name] = dict(passed=p.returncode == 0, tail=p.stdout[-400:])
        finally:
            srv.terminate()
    orig = res["정상1"]["passed"] and res["정상2"]["passed"]
    killed = [m for m in MUTANTS if not res[m]["passed"]] if orig else []
    return dict(orig=orig, killed=len(killed), killed_names=killed, detail=res)


def mcp_calls(key):
    n = 0
    for line in open(os.path.join(OUT, f"{key}_t1.jsonl"), encoding="utf-8"):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("type") == "assistant":
            for c in (e.get("message") or {}).get("content", []):
                if c.get("type") == "tool_use" and c.get("name", "").startswith("mcp__"):
                    n += 1
    return n


def score():
    for cname in CONDS:
        print(f"\n[{cname}]")
        for f in sorted(glob.glob(os.path.join(OUT, f"{cname}_r?.json"))):
            key = os.path.basename(f)[:-5]
            r = json.load(open(f, encoding="utf-8"))
            g = r["grade"]
            print(f"  정상 통과 {g.get('orig')}  잡은 고장 {g.get('killed')}/4 {g.get('killed_names', '')}  브라우저 호출 {mcp_calls(key)}  "
                  f"토큰 {r['tokens']['total_in'] + r['tokens']['output']:,}  시간 {r['turn']['sec']}초  rc {r['turn']['rc']}  {g.get('note', '')}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        keys = sys.argv[2:] or [f"{c}_r{r}" for r in range(1, 4) for c in CONDS]
        with ThreadPoolExecutor(max_workers=3) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
