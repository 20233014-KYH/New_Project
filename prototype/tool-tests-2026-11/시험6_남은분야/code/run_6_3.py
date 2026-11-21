#!/usr/bin/env python3
"""시험 6-3: ③ 코드 검색 — "큰 코드에서 어디를 고쳐야 할지 찾고 싶어요" (graphify / serena / codegraph)

- 코드: claude-mem 저장소(TypeScript, src 501개 파일, 전체 약 35만 줄, 커밋 b85cd12). tests/에도 같은 이름이 많아 헷갈리게 함.
- 질문 6개(정답은 코드에서 기계로 뽑음): 호출하는 파일 찾기 3개, 개념으로 찾기 2개(이름을 안 알려 줌), 바꾸면 영향 받는 파일 1개.
- 조건: none = Claude 기본 검색(Read·Grep·Glob) / graphify = 지식그래프 미리 만들고 graphify 안내문(CLAUDE.md) + graphify 명령 허용
        (serena·codegraph는 설치되면 CONDS에 추가해 같은 방식으로)
- 채점(AI 채점 없음): 파일 목록 질문은 F1(맞힌 비율·빠뜨린 비율), 개념 질문은 파일+함수 이름 맞으면 1. 토큰·시간.
사용법: python run_6_3.py setup <조건> | run [키 ...] | score     (이미 있는 결과는 건너뜀)
"""
import glob
import json
import os
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, r"C:\Users\User\Desktop\오픈소스_팀플\시험3_기획\code")
import run_plan_test_v3 as v3  # noqa: E402

v1 = v3.v1
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results_6_3")
CWDS = os.path.join(HERE, "_cwd_6_3")
REPO = r"C:\Users\User\Desktop\오픈소스_팀플\prototype\pilot_judgment\measure36\repos\thedotmack_claude-mem"
GRAPHIFY_BIN = r"C:\Users\User\tools\graphify-venv\Scripts"
GRAPHIFY_MD = r"C:\Users\User\tools\graphify-venv\Lib\site-packages\graphify\always_on\claude-md.md"
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
v1.ALLOWED = "Read,Glob,Grep,TodoWrite"
v1.DENIED = "PowerShell,WebFetch,WebSearch,Write,Edit"
os.environ["PATH"] = GRAPHIFY_BIN + os.pathsep + os.environ["PATH"]
os.environ["CODEGRAPH_TELEMETRY"] = "0"  # 사용 통계 보내기 끔

NPM = r"C:\Users\User\Desktop\오픈소스_팀플\prototype\pilot_judgment\measure36\npm\node_modules"
CODEGRAPH = os.path.join(NPM, "@colbymchenry", "codegraph", "npm-shim.js")
# graphify는 `cd 폴더 && graphify query ... | head`처럼 부르므로 cd·ls·head도 허용(1차에선 막혀서 graphify를 거의 못 씀 → graphify_v1)
EXTRA_ALLOW = {"none": "", "graphify": "Bash(graphify:*),Bash(graphify.exe:*),Bash(cd:*),Bash(ls:*),Bash(head:*)",
               "codegraph": "mcp__codegraph", "serena": "mcp__serena,ToolSearch"}  # serena 도구는 숨겨져 있다가 ToolSearch로 불러옴(1차엔 막혀서 무효)
SERENA = r"C:\Users\User\tools\serena-venv\Scripts\serena.exe"
MCP = {"codegraph": {"codegraph": {"command": "node", "args": [CODEGRAPH, "serve", "--mcp"]}}}
CONDS = ["none", "graphify", "codegraph", "serena"]


def serena_mcp(cwd):
    # serena 안내(README)의 Claude Code 연결 방식: start-mcp-server --context claude-code --project <폴더>
    return {"serena": {"command": SERENA, "args": ["start-mcp-server", "--context", "claude-code", "--project", cwd,
                                                   "--enable-web-dashboard", "false", "--open-web-dashboard", "false"]}}
# 주의: serena는 ~/.serena 폴더(전역 설정·메모)를 만든다(11/20 08:07 생김) → 시험 끝나면 지워서 원래대로
_prev = v1.subprocess.run
_allow_by_cwd, _mcp_by_cwd = {}, {}


def _run(cmd, **kw):
    cmd = list(cmd)
    if "--max-turns" in cmd:
        cmd[cmd.index("--max-turns") + 1] = "80"
    cfg = _mcp_by_cwd.get(kw.get("cwd"))
    if "--strict-mcp-config" in cmd and cfg:
        cmd += ["--mcp-config", json.dumps({"mcpServers": cfg})]
    extra = _allow_by_cwd.get(kw.get("cwd"))
    if extra and "--allowedTools" in cmd:
        cmd[cmd.index("--allowedTools") + 1] += "," + extra
    return _prev(cmd, **kw)


v1.subprocess.run = _run

# (종류, 질문, 정답을 뽑는 방법)
QUESTIONS = [
    ("callers", "killProcessTree 함수를 직접 부르는 src/ 안의 파일을 전부 알려 줘(정의한 파일·테스트 제외).", "killProcessTree"),
    ("callers", "ensureServerStorageSchema 함수를 직접 부르는 src/ 안의 파일을 전부 알려 줘(정의한 파일·테스트 제외).", "ensureServerStorageSchema"),
    ("callers", "captureEvent 함수를 직접 부르는 src/ 안의 파일을 전부 알려 줘(정의한 파일·테스트 제외).", "captureEvent"),
    ("concept", "텔레메트리(사용 통계) 동의 설정을 불러오는 함수는 어느 파일의 무슨 함수야?",
     ("src/services/telemetry/consent.ts", "loadTelemetryConfig")),
    ("concept", "저장할 내용에서 메모리 태그(예: 비공개로 표시한 부분)를 지워 주는 함수는 어느 파일의 무슨 함수야? (JSON 문자열용 말고 기본 함수)",
     ("src/utils/tag-stripping.ts", "stripMemoryTags")),
    ("callers", "expandHome 함수가 동작을 바꾸면 직접 영향을 받는(이 함수를 부르는) src/ 안의 파일을 전부 알려 줘(정의한 파일·테스트 제외).", "expandHome"),
]


def src_files(root):
    out = {}
    for r, ds, fs in os.walk(os.path.join(root, "src")):
        for f in fs:
            if f.endswith(".ts"):
                p = os.path.join(r, f)
                out[os.path.relpath(p, root).replace(os.sep, "/")] = open(p, encoding="utf-8", errors="replace").read()
    return out


def truth(root):
    files = src_files(root)
    res = []
    for kind, _, key in QUESTIONS:
        if kind == "callers":
            # 같은 이름의 함수를 따로 정의한 파일(예: CodexCliInstaller.ts의 자체 expandHome)은 호출한 곳이 아님
            defs = [p for p, t in files.items() if re.search(r"function " + key + r"\b", t)]
            res.append(sorted(p for p, t in files.items() if p not in defs and re.search(r"\b" + key + r"\s*\(", t)))
        else:
            res.append(list(key))
    return res


def setup(cname):
    cwd = os.path.join(CWDS, cname)
    if os.path.exists(os.path.join(cwd, ".ready")):
        return cwd
    shutil.rmtree(cwd, ignore_errors=True)
    shutil.copytree(REPO, cwd, ignore=shutil.ignore_patterns(".git", "node_modules"))
    # 저장소에 원래 있는 CLAUDE.md는 둔다(사람들이 받는 그대로). graphify는 설치할 때처럼 안내문을 덧붙인다.
    if cname == "graphify":
        r = v1.subprocess.run([os.path.join(GRAPHIFY_BIN, "graphify.exe"), "extract", ".", "--code-only"], cwd=cwd,
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3000)
        print(r.stdout[-500:], r.stderr[-500:])
        with open(os.path.join(cwd, "CLAUDE.md"), "a", encoding="utf-8") as f:
            f.write("\n\n" + open(GRAPHIFY_MD, encoding="utf-8").read())
    if cname == "codegraph":
        # 설치 안내대로: 프로젝트 색인(init) + MCP 연결. 설치기가 CLAUDE.md에 넣는 짧은 안내는 MCP가 연결 때 주는 안내와 같은 내용이라 생략
        r = v1.subprocess.run(["node", CODEGRAPH, "init", "-y", "--local-only", "."], cwd=cwd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=3000)
        print(r.stdout[-800:], r.stderr[-500:])
    open(os.path.join(cwd, ".ready"), "w").write("ok")
    return cwd


def prompt():
    qs = "\n".join(f"Q{i}. {q}" for i, (_, q, _) in enumerate(QUESTIONS, 1))
    return (f"이 저장소 코드에 대해 물어볼게. 코드는 고치지 말고 찾아서 답만 해.\n{qs}\n"
            "답은 맨 끝에 `A1: 파일경로, 파일경로` 형식으로 한 줄씩 적어 줘(경로는 저장소 기준, 예: src/shared/paths.ts). "
            "함수를 묻는 질문은 `A4: 파일경로 함수이름`.")


def parse(text):
    got = {}
    for m in re.finditer(r"^\s*\**A(\d)\**\s*[:：]\s*(.+)$", text, re.M):
        got[int(m.group(1))] = m.group(2)
    return got


def grade(t, got):
    sc = []
    for i, ((kind, _, _), ans) in enumerate(zip(QUESTIONS, t), 1):
        line = got.get(i, "")
        if kind == "callers":
            paths = set(re.findall(r"src/[\w./-]+\.ts", line))
            tp = len(paths & set(ans))
            p = tp / len(paths) if paths else 0
            r = tp / len(ans) if ans else 0
            sc.append(round(2 * p * r / (p + r), 3) if p + r else 0)
        else:
            sc.append(1.0 if ans[0] in line and ans[1] in line else 0.0)
    return sc


def run_one(key):
    cname, rep = key.rsplit("_", 1)
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    cwd = setup(cname)
    _allow_by_cwd[cwd] = EXTRA_ALLOW[cname]
    _mcp_by_cwd[cwd] = serena_mcp(cwd) if cname == "serena" else MCP.get(cname)
    t = v1.run_turn(cwd, {}, prompt(), key, 1)
    text = t.get("result") or "\n".join(t["texts"][-2:])
    tr = truth(cwd)
    got = parse(text)
    sc = grade(tr, got)
    jl = os.path.join(OUT, f"{key}_t1.jsonl")
    calls = {}
    for line in open(jl, encoding="utf-8", errors="replace"):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("type") == "assistant":
            for c in (e.get("message") or {}).get("content", []):
                if c.get("type") == "tool_use":
                    n = c.get("name")
                    if n == "Bash":
                        n = "Bash:" + (c.get("input") or {}).get("command", "").split()[0]
                    calls[n] = calls.get(n, 0) + 1
    u = v1.tokens(t["usage"])
    rec = dict(condition=cname, rep=int(rep), sec=t["sec"], rc=t["rc"], turns=t["turns"],
               tokens=u["input"] + u["cache_create"] + u["cache_read"] + u["output"], usage=u,
               truth=tr, got=got, scores=sc, total=round(sum(sc), 2), calls=calls, result=text[-2000:])
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: {rec['total']}/6  토큰 {rec['tokens']:,}  {t['sec']:.0f}초  도구 {calls}"


def score():
    tr = truth(os.path.join(CWDS, "none"))  # 정답을 고치면 저장된 답으로 다시 채점
    for cname in CONDS:
        rs = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(OUT, f"{cname}_?.json")))]
        for r in rs:
            r["scores"] = grade(tr, {int(k): v for k, v in r["got"].items()})
            r["total"] = round(sum(r["scores"]), 2)
        if rs:
            print(f"[{cname}] 점수 " + " / ".join(f"{r['total']}/6" for r in rs) +
                  f"  평균 토큰 {sum(r['tokens'] for r in rs) // len(rs):,}  평균 {sum(r['sec'] for r in rs) / len(rs):.0f}초"
                  f"  문항별 {[r['scores'] for r in rs]}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    elif sys.argv[1] == "setup":
        for c in sys.argv[2:]:
            print(c, setup(c))
    else:
        keys = sys.argv[2:] or [f"{c}_{r}" for r in range(1, 4) for c in CONDS]
        with ThreadPoolExecutor(max_workers=2) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
