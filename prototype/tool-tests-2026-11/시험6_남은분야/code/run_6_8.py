#!/usr/bin/env python3
"""시험 6-8: ⑤ 인프라 — terraform-mcp-server가 강하다는 상황(레지스트리에서 최신 provider·문서를 바로 찾음)

- 과제: main.tf 쓰기 — hashicorp/random·local·time 세 provider를 "지금 나와 있는 최신 버전" 기준 `~> 메이저.마이너`로 고정하고,
  random_pet 이름을 local_file로 파일에 쓰고, time_static으로 만든 시각을 output으로 내보내기.
  terraform을 실행해 볼 수 없게 함(한 번에 써야 함). 웹 검색 없음.
- 조건: none / tfmcp(terraform-mcp-server 1.4.1, 공식 안내대로 stdio, 토큰 없이 공개 레지스트리 도구만)
- 채점(AI 채점 없음): ① terraform init·validate 통과 ② 세 provider 버전 제약이 레지스트리 최신 메이저.마이너와 같음(3점) → 4점
  최신 버전은 채점 때 레지스트리 API로 확인.
사용법: python run_6_8.py run [키 ...] | score     (이미 있는 결과는 건너뜀)
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, r"C:\Users\User\Desktop\오픈소스_팀플\시험3_기획\code")
import run_plan_test_v3 as v3  # noqa: E402

v1 = v3.v1
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results_6_8")
CWDS = os.path.join(HERE, "_cwd_6_8")
TF = r"C:\Users\User\tools\terraform\terraform.exe"
TFMCP = r"C:\Users\User\tools\terraform\terraform-mcp-server.exe"
CACHE = os.path.join(HERE, "_tf_plugin_cache")
os.makedirs(OUT, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)
v1.OUT = OUT
v1.ALLOWED = "Read,Glob,Grep,Write,Edit,TodoWrite"
v1.DENIED = "PowerShell,WebFetch,WebSearch,Bash"
PROVIDERS = ["random", "local", "time"]
CONDS = ["none", "tfmcp"]
PROMPT = ("이 폴더에 Terraform 설정 main.tf를 만들어 줘. hashicorp/random, hashicorp/local, hashicorp/time 세 provider를 "
          "지금 나와 있는 최신 버전 기준으로 `~> 메이저.마이너` 형태로 고정해 줘(예: 최신이 4.2.3이면 \"~> 4.2\"). "
          "random_pet으로 이름을 하나 만들어 local_file로 pet.txt 파일에 쓰고, time_static으로 만든 시각을 output \"created_at\"으로 내보내. "
          "지금은 terraform을 실행해 볼 수 없으니 한 번에 맞게 써 줘.")
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


def latest(p):
    with urllib.request.urlopen(f"https://registry.terraform.io/v1/providers/hashicorp/{p}/versions", timeout=30) as r:
        vs = [v["version"] for v in json.load(r)["versions"] if "-" not in v["version"]]
    vs.sort(key=lambda v: [int(x) for x in v.split(".")])
    return vs[-1]


def grade(cwd):
    g = dict(validate=False, versions={}, latest={}, error=None)
    tf = os.path.join(cwd, "main.tf")
    if not os.path.exists(tf):
        g.update(error="main.tf 없음", score=0)
        return g
    src = open(tf, encoding="utf-8").read()
    env = dict(os.environ, TF_PLUGIN_CACHE_DIR=CACHE, CHECKPOINT_DISABLE="1", TF_IN_AUTOMATION="1")
    r1 = subprocess.run([TF, "init", "-input=false", "-no-color"], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=600)
    r2 = subprocess.run([TF, "validate", "-no-color"], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=300) if r1.returncode == 0 else None
    g["validate"] = bool(r2 and r2.returncode == 0)
    if not g["validate"]:
        g["error"] = ((r2.stdout + r2.stderr) if r2 else (r1.stdout + r1.stderr))[-500:]
    ok = 0
    for p in PROVIDERS:
        lv = latest(p)
        g["latest"][p] = lv
        m = re.search(r'source\s*=\s*"hashicorp/' + p + r'"\s*\n\s*version\s*=\s*"([^"]+)"', src) or \
            re.search(r'version\s*=\s*"([^"]+)"\s*\n\s*source\s*=\s*"hashicorp/' + p + '"', src)
        v = m.group(1) if m else None
        g["versions"][p] = v
        mm = ".".join(lv.split(".")[:2])
        if v and re.fullmatch(r"~>\s*" + re.escape(mm) + r"(\.0)?", v.strip()):
            ok += 1
    g["versions_ok"] = ok
    g["score"] = int(g["validate"]) + ok
    return g


def run_one(key):
    cname, rep = key.rsplit("_", 1)
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    cwd = os.path.join(CWDS, key)
    shutil.rmtree(cwd, ignore_errors=True)
    os.makedirs(cwd, exist_ok=True)
    if cname == "tfmcp":
        _mcp_by_cwd[cwd] = {"terraform": {"command": TFMCP, "args": ["stdio"]}}
        _allow_by_cwd[cwd] = "mcp__terraform"
    t = v1.run_turn(cwd, {}, PROMPT, key, 1)
    g = grade(cwd)
    jl = os.path.join(OUT, f"{key}_t1.jsonl")
    mcp = sum(1 for line in open(jl, encoding="utf-8", errors="replace") if '"name":"mcp__terraform' in line and '"tool_use"' in line)
    u = v1.tokens(t["usage"])
    tf = os.path.join(cwd, "main.tf")
    rec = dict(condition=cname, rep=int(rep), sec=t["sec"], rc=t["rc"], turns=t["turns"],
               tokens=u["input"] + u["cache_create"] + u["cache_read"] + u["output"], usage=u, grade=g, mcp_calls=mcp,
               main_tf=open(tf, encoding="utf-8").read()[:3000] if os.path.exists(tf) else None, result=(t.get("result") or "")[-600:])
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: {g['score']}/4  버전 {g['versions']}  최신 {g['latest']}  토큰 {rec['tokens']:,}  {t['sec']:.0f}초  MCP {mcp}번"


def score():
    for cname in CONDS:
        rs = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(OUT, f"{cname}_?.json")))]
        if rs:
            n = len(rs)
            print(f"[{cname}] 점수 {[r['grade']['score'] for r in rs]}  validate {[r['grade']['validate'] for r in rs]}"
                  f"  버전 {[r['grade']['versions'] for r in rs]}  평균 토큰 {sum(r['tokens'] for r in rs) // n:,}"
                  f"  평균 {sum(r['sec'] for r in rs) / n:.0f}초  MCP {[r['mcp_calls'] for r in rs]}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        keys = sys.argv[2:] or [f"{c}_{r}" for r in range(1, 4) for c in CONDS]
        with ThreadPoolExecutor(max_workers=2) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
