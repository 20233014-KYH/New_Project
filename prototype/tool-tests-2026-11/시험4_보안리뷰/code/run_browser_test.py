#!/usr/bin/env python3
"""시험 4-2: 브라우저 도구. "추가 버튼을 눌러도 안 돼"의 진짜 원인(투명한 .toast-layer가 버튼을 덮음)을 찾나.

- 과제: fixture_web(로컬 서버로 띄움). 코드 파일도 같은 폴더에 있어서 도구 없이 읽어서도 찾을 수 있다.
- 조건: none 도구 없음(명령도 막음) / curl 그 사이트에만 curl 허용 / pw playwright-mcp / cdt chrome-devtools-mcp
  (브라우저 도구는 headless·isolated, 이 실행에만 연결)
- 명령 실행 없음(읽기와 브라우저 도구만). 깨끗한 환경은 시험 3 v3와 같음
사용법: python run_browser_test.py run [키 ...] | score
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
OUT = os.path.join(HERE, "..", "results_browser")
CWDS = os.path.join(HERE, "_cwd_browser")
NPM = r"C:\Users\User\Desktop\오픈소스_팀플\prototype\pilot_judgment\measure36\npm\node_modules"
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
v1.ALLOWED = "Read,Glob,Grep,TodoWrite,mcp__playwright,mcp__chrome-devtools"
v1.DENIED = "Bash,PowerShell,Write,Edit,WebFetch,WebSearch"

MCP = {
    "pw": {"playwright": {"command": "node", "args": [os.path.join(NPM, "@playwright", "mcp", "cli.js"), "--headless", "--isolated"]}},
    "cdt": {"chrome-devtools": {"command": "node", "args": [os.path.join(NPM, "chrome-devtools-mcp", "build", "src", "bin", "chrome-devtools-mcp.js"), "--headless", "--isolated"]}},
}
# curl: 브라우저 도구 없이, 그 사이트 주소에만 curl을 허용(기본 Claude가 명령으로 페이지를 받아 읽는 경우)
CONDS = ["none", "curl", "pw", "cdt"]

# 실행마다 다른 MCP 설정·허용 명령을 붙이기 위해, 시험 3 장치의 subprocess.run 감싸기 위에 한 겹 더 감싼다
_mcp_by_cwd = {}
_allow_by_cwd = {}
_lock = threading.Lock()
_prev = v1.subprocess.run


def _run(cmd, **kw):
    cmd = list(cmd)
    cfg = _mcp_by_cwd.get(kw.get("cwd"))
    if "--strict-mcp-config" in cmd and cfg:
        cmd += ["--mcp-config", json.dumps({"mcpServers": cfg})]
    extra = _allow_by_cwd.get(kw.get("cwd"))
    if extra and "--allowedTools" in cmd:
        i = cmd.index("--allowedTools") + 1
        cmd[i] += "," + extra
        j = cmd.index("--disallowedTools") + 1
        cmd[j] = cmd[j].replace("Bash,", "")
    return _prev(cmd, **kw)


v1.subprocess.run = _run


def run_one(key):
    cname, rep = key.rsplit("_r", 1)
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    i = CONDS.index(cname) * 3 + int(rep)
    port = 8810 + i
    # 코드는 주지 않는다(배포된 사이트 상황): 페이지는 다른 폴더에서 띄우고, 작업 폴더는 비워 둔다.
    # 처음엔 코드를 같은 폴더에 뒀더니 브라우저 없이 코드만 읽어서 풀려 도구 차이가 안 보였다.
    cwd = os.path.join(CWDS, key)
    site = cwd + "_site"
    for d in (cwd, site):
        shutil.rmtree(d, ignore_errors=True)
    os.makedirs(cwd)
    shutil.copytree(os.path.join(HERE, "fixture_web"), site)
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=site,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        with _lock:
            _mcp_by_cwd[cwd] = MCP.get(cname)
            if cname == "curl":
                # Claude Code 허용 규칙은 "앞부분:*" 형식(처음엔 /*로 써서 curl이 막혔음 → results_browser/_curl_rule_wrong/)
                # 앞부분이 일치해야 해서 자주 쓰는 옵션 조합을 모두 넣는다(주소는 이 사이트만)
                # 주소에 ":"가 들어 있어 "앞부분:*" 규칙이 안 맞았다 → 별표(*) 패턴으로 이 사이트 주소가 들어간 curl만 허용
                _allow_by_cwd[cwd] = f"Bash(curl *127.0.0.1:{port}*),Bash(head *)"
        prompt = (f"배포된 사이트 http://127.0.0.1:{port}/ 에서 할 일을 입력하고 '추가' 버튼을 눌러도 목록에 추가되지 않아. "
                  "코드는 나한테 없어. 원인을 찾아 줘. 원인만 알려 주면 돼.")
        t = v1.run_turn(cwd, {}, prompt, key, 1)
    finally:
        srv.terminate()
    u = v1.tokens(t["usage"])
    rec = dict(condition=cname, rep=int(rep), turn=t, tokens=dict(total_in=u["input"] + u["cache_create"] + u["cache_read"], output=u["output"]))
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: 끝 ({t['sec']}초, rc={t['rc']}, 출력={u['output']})"


def mcp_calls(key):
    n, names = 0, set()
    for line in open(os.path.join(OUT, f"{key}_t1.jsonl"), encoding="utf-8"):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("type") == "assistant":
            for c in (e.get("message") or {}).get("content", []):
                if c.get("type") == "tool_use" and c.get("name", "").startswith("mcp__"):
                    n += 1
                    names.add(c["name"].split("__")[-1])
    return n, sorted(names)


def score():
    for cname in CONDS:
        rows = []
        for f in sorted(glob.glob(os.path.join(OUT, f"{cname}_r?.json"))):
            key = os.path.basename(f)[:-5]
            r = json.load(open(f, encoding="utf-8"))
            text = (r["turn"].get("result") or "") + "\n".join(r["turn"]["texts"])
            found = 1 if re.search(r"toast-layer|오버레이|overlay|덮|가로막|가려|pointer-events|z-index|intercept", text, re.I) else 0
            n, names = mcp_calls(key)
            rows.append((found, n, r["tokens"]["total_in"] + r["tokens"]["output"], r["turn"]["sec"], r["turn"]["rc"], names))
        print(f"{cname:<5} 원인 맞힘 {[x[0] for x in rows]}  브라우저 도구 호출 {[x[1] for x in rows]}  토큰 {[x[2] for x in rows]}  "
              f"시간 {[x[3] for x in rows]}  rc {[x[4] for x in rows]}  쓴 도구 {[x[5][:4] for x in rows]}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        keys = sys.argv[2:] or [f"{c}_r{r}" for r in range(1, 4) for c in CONDS]
        with ThreadPoolExecutor(max_workers=3) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
