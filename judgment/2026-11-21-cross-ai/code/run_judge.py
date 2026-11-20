"""묶음마다 판정자(claude / codex)에게 판정지시문 + 묶음을 주고 결과를 out/{judge}/{batch}.json에 저장.
이미 결과가 있으면 건너뛴다(끊겨도 이어서). 사용: python run_judge.py claude|codex|both
"""
import json, os, re, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUIDE = open(os.path.join(HERE, "판정지시문.md"), encoding="utf-8").read()
CLAUDE = os.path.expanduser("~/.local/bin/claude.exe")
WORK = tempfile.mkdtemp(prefix="judge_")   # 빈 폴더에서 실행(프로젝트 파일을 읽지 않게)

def prompt(b):
    return (GUIDE + "\n\n## 도구 정보\n" + json.dumps(b["tools"], ensure_ascii=False)
            + f"\n\n## 판정할 쌍 ({len(b['pairs'])}개, 이 순서대로 전부)\n" + json.dumps(b["pairs"], ensure_ascii=False))

def parse(text, b):
    s, e = text.find("["), text.rfind("]")
    arr = json.loads(text[s:e + 1])
    want = {(p["a"], p["b"]) for p in b["pairs"]}
    got = {(x["a"], x["b"]) for x in arr}
    if want - got:
        raise ValueError(f"빠진 쌍 {len(want - got)}개: {sorted(want - got)[:3]}")
    return [x for x in arr if (x["a"], x["b"]) in want]

def run_claude(p):
    env = dict(os.environ, CLAUDE_CONFIG_DIR=os.path.expanduser("~/.claude-clean"))
    r = subprocess.run([CLAUDE, "-p", "--model", "sonnet", "--output-format", "json", "--setting-sources", "project",
                        "--settings", "{}", "--strict-mcp-config",
                        "--disallowedTools", "Bash,Edit,Write,Read,Glob,Grep,WebFetch,WebSearch,Task,NotebookEdit"],
                       input=p, cwd=WORK, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1200)
    j = json.loads(r.stdout)
    u = j.get("usage") or {}
    return j.get("result", ""), {"input": u.get("input_tokens", 0), "cache_create": u.get("cache_creation_input_tokens", 0),
                                 "cache_read": u.get("cache_read_input_tokens", 0), "output": u.get("output_tokens", 0)}

def run_codex(p):
    out = os.path.join(WORK, f"codex_{time.time_ns()}.txt")
    r = subprocess.run(["codex", "exec", "--skip-git-repo-check", "-s", "read-only", "-o", out, "-"],
                       input=p, cwd=WORK, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1200, shell=True)
    m = re.search(r"tokens used\s*\n?\s*([\d,]+)", r.stdout + r.stderr)
    return open(out, encoding="utf-8").read(), {"total": int(m.group(1).replace(",", "")) if m else None}

def job(judge, name):
    dst = os.path.join(HERE, "out", judge, name)
    if os.path.exists(dst):
        return f"{judge} {name} 이미 있음"
    b = json.load(open(os.path.join(HERE, "batches", name), encoding="utf-8"))
    last = ""
    for attempt in range(2):
        t0 = time.time()
        try:
            text, usage = (run_claude if judge == "claude" else run_codex)(prompt(b))
            res = parse(text, b)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            json.dump({"batch": b["batch"], "judge": judge, "sec": round(time.time() - t0), "usage": usage, "pairs": res},
                      open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            return f"{judge} {name} 끝 {round(time.time() - t0)}초 {usage}"
        except Exception as ex:
            last = repr(ex)[:300]
    return f"{judge} {name} 실패: {last}"

if __name__ == "__main__":
    judges = ["claude", "codex"] if sys.argv[1] == "both" else [sys.argv[1]]
    names = sorted(os.listdir(os.path.join(HERE, "batches")))
    only = sys.argv[2:]   # 묶음 이름을 주면 그것만
    if only:
        names = [n for n in names if n in only]
    with ThreadPoolExecutor(4) as ex:
        for msg in ex.map(lambda jn: job(*jn), [(j, n) for j in judges for n in names]):
            print(msg, flush=True)
