#!/usr/bin/env python3
"""시험 6-5: ② 여러 세션 기억 — claude-mem vs planning-with-files vs 없음 (시험 5 R5와 같은 과제)

R5 = 동아리 회비 계산기를 6세션에 나눠 만듦(세션마다 새로 시작, 대화 기억 없음). 세션 1·3에 말로만 정한 규칙을 뒤 세션에서도 지키나 → 숨은 테스트 16개.
- claude-mem 16.0.1: 공식 설치기로 받은 플러그인(`C:/Users/User/tools/claude-mem-plugin16`)을 --plugin-dir로. 기억 요약 모델 = claude(haiku, 내 구독).
  **전역 설정을 안 건드리게** 시험 프로세스에만: LOCALAPPDATA·CLAUDE_MEM_DATA_DIR를 실행마다 따로 주고, 런처 폴더·bun·uv를 그 프로세스 PATH에만 넣음
  (설치기·훅이 사용자 Path를 고친 일이 있어 되돌렸음 → 진행기록 참고). 통계 보내기 끔.
- 같은 날 비교를 위해 none·pwf도 다시 돌림(11/13 R5 결과와 모델 버전이 다를 수 있음).
- 채점: R5 그대로(숨은 테스트 16개, 규칙 묶음별) + 토큰. claude-mem은 뒤에서 도는 요약 모델 토큰(로그의 Observer turn usage)도 따로 더함.
사용법: python run_6_5.py run [키 ...] | score     키 예: cmem_r2   (이미 있는 결과는 건너뜀)
"""
import glob
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, r"C:\Users\User\Desktop\오픈소스_팀플\시험5_재설계\code")
import run_r5 as r5  # noqa: E402

v1 = r5.v1
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results_6_5")
CWDS = os.path.join(HERE, "_cwd_6_5")
os.makedirs(OUT, exist_ok=True)
r5.OUT, r5.CWDS = OUT, CWDS
v1.OUT = OUT
PLUGIN = r"C:\Users\User\tools\claude-mem-plugin16"
BUN = r"C:\Users\User\tools\bun\bun-windows-x64"
UV = r"C:\Users\User\tools\uv"
r5.CONDITIONS["cmem"] = dict(plugins=[PLUGIN])
CONDS = ["none", "pwf", "cmem"]
_env_by_cwd = {}
_prev = v1.subprocess.run


def iso_dir(key):
    return os.path.join(CWDS, key + "_cmem")


def _run(cmd, **kw):
    e = _env_by_cwd.get(kw.get("cwd"))
    if e is not None and "--settings" in list(cmd):
        kw["env"] = e
    return _prev(cmd, **kw)


v1.subprocess.run = _run


def make_env(key):
    d = iso_dir(key)
    lad, data = os.path.join(d, "lad"), os.path.join(d, "data")
    os.makedirs(os.path.join(lad, "claude-mem", "bin"), exist_ok=True)
    os.makedirs(data, exist_ok=True)
    return dict(os.environ, LOCALAPPDATA=lad, CLAUDE_MEM_DATA_DIR=data, CLAUDE_MEM_TELEMETRY="0", CLAUDE_MEM_ONLINE_OPTIN="false",
                DO_NOT_TRACK="1", PATH=os.pathsep.join([os.path.join(lad, "claude-mem", "bin"), BUN, UV, os.environ["PATH"]]))


def observer_tokens(key):
    tot = 0
    for f in glob.glob(os.path.join(iso_dir(key), "data", "logs", "*.log")):
        for line in open(f, encoding="utf-8", errors="replace"):
            if "Observer turn usage" in line:
                for k in ("inputTokens", "cacheCreationInputTokens", "cacheReadInputTokens", "outputTokens"):
                    m = re.search(r"\b" + k + r"=(\d+)", line)
                    tot += int(m.group(1)) if m else 0
    return tot


def stop_worker(key):
    pidf = os.path.join(iso_dir(key), "data", "worker.pid")
    if not os.path.exists(pidf):
        return
    txt = open(pidf, encoding="utf-8").read().strip()
    try:
        p = json.loads(txt).get("pid") if txt.startswith("{") else int(txt)
    except Exception:
        p = None
    if p:
        subprocess.run(["taskkill", "/PID", str(p), "/T", "/F"], capture_output=True)


def run_one(key):
    cname = key.rsplit("_r", 1)[0]
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    cwd = os.path.join(CWDS, key)
    if cname == "cmem":
        _env_by_cwd[cwd] = make_env(key)
    try:
        msg = r5.run_one(key)
    finally:
        if cname == "cmem":
            stop_worker(key)
    if cname == "cmem" and os.path.exists(out):
        rec = json.load(open(out, encoding="utf-8"))
        rec["observer_tokens"] = observer_tokens(key)
        json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        msg += f"  (기억 요약 모델 토큰 {rec['observer_tokens']:,})"
    return msg


def score():
    for cname in CONDS:
        print(f"\n[{cname}]")
        for f in sorted(glob.glob(os.path.join(OUT, f"{cname}_r?.json"))):
            r = json.load(open(f, encoding="utf-8"))
            h = r["hidden"]
            by = {g: sum(1 for k, v in h.items() if k.startswith(p) and v) for g, p in r5.GROUPS.items()}
            tok = sum(s["tokens"] for s in r["sessions"])
            sec = sum(s["sec"] for s in r["sessions"])
            extra = f"  +요약 {r['observer_tokens']:,}" if "observer_tokens" in r else ""
            print(f"  숨은 {sum(h.values())}/16  " + "  ".join(f"{g} {by[g]}/{r5.GROUP_N[g]}" for g in r5.GROUPS) +
                  f"  자기테스트 {''.join('O' if s['own_tests_ok'] else 'X' for s in r['sessions'])}  토큰 {tok:,}{extra}  시간 {sec / 60:.0f}분")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        keys = sys.argv[2:] or [f"{c}_r{r}" for r in range(1, 4) for c in CONDS]
        with ThreadPoolExecutor(max_workers=3) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
