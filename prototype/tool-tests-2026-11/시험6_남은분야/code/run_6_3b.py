#!/usr/bin/env python3
"""시험 6-3b: ③ 코드 이해 — 도구들이 "강하다"고 말하는 상황에서 맞대결 (graphify vs codegraph vs serena vs 없음)

같은 claude-mem 저장소, 6-3에서 만든 색인을 그대로 씀.
- T1 흐름 질문(codegraph·graphify가 강하다는 상황 — "X는 어떻게 동작해?"):
  "captureEvent로 만든 사용 통계 이벤트가 PostHog로 보내지기 전까지 거치는 단계" → 정답표 6개(Claude가 만들고 Codex가 따로 확인:
  codex_상의/6-3b_T1_정답표.txt). 채점 = 답에 나온 정답 함수 수(0~6) + 토큰·도구 호출·읽은 파일 수.
- T2 여러 파일 이름 바꾸기(serena가 강하다는 상황 — 심볼 단위 리팩터링):
  공용 expandHome(src/shared/expand-home.ts)을 resolveHomePath로. 함정 = 같은 이름의 다른 함수 2개
  (CodexCliInstaller.ts, transcripts/config.ts)는 바꾸면 안 됨. 채점 4점: 정의 바뀜 / 쓰는 파일 전부 바뀜 / 함정 그대로 / 엉뚱한 파일 안 건드림.
사용법: python run_6_3b.py run [키 ...] | score     키 예: T1_codegraph_1, T2_serena_2   (이미 있는 결과는 건너뜀)
"""
import glob
import json
import os
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor

import run_6_3 as base  # 조건 설정(그래프·색인·MCP·허용 도구)을 그대로 씀

v1 = base.v1
HERE = base.HERE
OUT = os.path.join(HERE, "..", "results_6_3b")
TMP = os.path.join(HERE, "_cwd_6_3b")
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
CONDS = ["none", "graphify", "codegraph", "serena", "serenaask"]
# serenaask = serena 표준 설치 + "Serena로 해 줘"라고 직접 시킴(serena 문서: 일부 모델은 이렇게 말해 줘야 함). 표준 설치만으로는 모델이 serena를 안 씀.
ASK = "Serena 도구를 써서 해 줘(먼저 Serena의 initial_instructions를 읽어). "

T1_PROMPT = ("이 저장소에서 src/services/telemetry/telemetry.ts의 captureEvent로 만든 사용 통계 이벤트가 실제로 PostHog로 보내지기 전까지 "
             "어떤 단계를 거치는지 알려 줘. 단계마다 파일 경로와 함수 이름을 순서대로 적어 줘. 코드는 고치지 마.")
# T3 = Codex 제안(codex_상의/6-3b_T1_해석.txt): 시작 파일·함수를 안 알려 주는 넓은 흐름 질문(codegraph README의 질문 모양). 정답은 T1과 같음.
T3_PROMPT = ("이 저장소에서 사용 통계(텔레메트리) 이벤트를 모아서 PostHog로 보내는 처리 경로를 설명해 줘. "
             "모으는 입구부터 실제로 보내는 호출까지 순서대로, 단계마다 파일 경로와 함수 이름을 근거로 적어 줘. 코드는 고치지 마.")
T1_KEYS =["hasConsent", "buildBaseProperties", "scrubProperties", "getClient", "getOrCreateInstallId", "errorBeforeSend"]
T2_PROMPT = ("src/shared/expand-home.ts의 expandHome 함수 이름을 resolveHomePath로 바꿔 줘. 이 함수를 가져다 쓰는 곳(src·tests 전부)도 "
             "같이 바꿔 줘. 같은 이름이라도 다른 파일에 따로 만들어진 함수는 건드리면 안 돼. 다 바꾸면 바꾼 파일 목록을 알려 줘.")
TRAPS = ["src/services/integrations/CodexCliInstaller.ts", "src/services/transcripts/config.ts"]
DEF = "src/shared/expand-home.ts"


def all_ts(root):
    out = {}
    for r, ds, fs in os.walk(root):
        ds[:] = [d for d in ds if d not in ("node_modules", ".codegraph", "graphify-out", ".git", ".serena")]
        for f in fs:
            if f.endswith((".ts", ".tsx", ".mts")):
                p = os.path.join(r, f)
                out[os.path.relpath(p, root).replace(os.sep, "/")] = open(p, "rb").read()
    return out


# 채점표: Claude 1차 → 시험해 보니 애매(re-export·비슷한 이름) → Codex가 코드 보고 따로 정리(codex_상의/6-3b_T2_채점표.txt)해서 합의한 것
MUST = ["src/shared/paths.ts", "src/integrations/harness-worker.ts", "src/services/integrations/DeepSeekHarnessInstaller.ts",
        "src/services/memory/cli.ts", "src/services/memory/ingest.ts", "src/utils/project-filter.ts", "src/utils/project-name.ts",
        "tests/shared/paths.test.ts"]
KEEP = {"src/services/integrations/CodexCliInstaller.ts": rb"function expandHome\b",  # 같은 이름 별도 함수
        "src/services/transcripts/config.ts": rb"function expandHomePath\b",
        "src/shared/paths.ts": rb"\bexpandTilde\b"}
COMMENT_ONLY = ["src/services/transcripts/config.ts", "tests/transcripts/config.test.ts", "tests/utils/project-filter.test.ts"]


def code_only(b):
    return re.sub(rb"//[^\n]*", b"", re.sub(rb"/\*.*?\*/", b"", b, flags=re.S))


def grade_t2(before, after):
    d = code_only(after.get(DEF, b""))
    g = dict(definition=bool(re.search(rb"function resolveHomePath\b", d)) and not re.search(rb"\bexpandHome\b", d))
    ok = [p for p in MUST if re.search(rb"\bresolveHomePath\b", after.get(p, b"")) and not re.search(rb"\bexpandHome\b", code_only(after.get(p, b"")))]
    g["callers_all"] = len(ok) == len(MUST)
    g["callers_done"] = len(ok)
    g["callers_total"] = len(MUST)
    cx = "src/services/integrations/CodexCliInstaller.ts"
    g["traps_untouched"] = (all(re.search(pat, after.get(p, b"")) for p, pat in KEEP.items())
                            and not re.search(rb"resolveHomePath", after.get(cx, b"")))
    changed = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
    g["changed"] = changed
    g["stray"] = [p for p in changed if p not in MUST and p != DEF and p not in COMMENT_ONLY]
    g["no_stray"] = not g["stray"]
    g["score"] = sum(g[k] for k in ("definition", "callers_all", "traps_untouched", "no_stray"))
    return g


def tool_stats(jl):
    calls, reads = {}, 0
    for line in open(jl, encoding="utf-8", errors="replace"):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if not isinstance(e, dict) or e.get("type") != "assistant":
            continue
        for c in (e.get("message") or {}).get("content", []) or []:
            if isinstance(c, dict) and c.get("type") == "tool_use":
                n = c.get("name")
                if n == "Bash":
                    n = "Bash:" + ((c.get("input") or {}).get("command", "").split() or ["?"])[0]
                calls[n] = calls.get(n, 0) + 1
                reads += n == "Read"
    return calls, reads


def own_calls(calls):
    return sum(v for k, v in calls.items() if k.startswith("mcp__") or k.startswith("Bash:graphify"))


def run_one(key):
    task, cname, rep = key.split("_")
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    real = "serena" if cname == "serenaask" else cname
    src = base.setup(real)
    if task in ("T1", "T3"):
        cwd = src  # 읽기만 함 → 준비된 폴더 그대로
        allow = base.EXTRA_ALLOW[real]
    else:
        cwd = os.path.join(TMP, key)  # 고치는 과제 → 매번 새 복사본(색인 포함)
        shutil.rmtree(cwd, ignore_errors=True)
        shutil.copytree(src, cwd)
        allow = ",".join(x for x in [base.EXTRA_ALLOW[real], "Edit", "Write", "MultiEdit"] if x)
    base._allow_by_cwd[cwd] = allow
    base._mcp_by_cwd[cwd] = base.serena_mcp(cwd) if real == "serena" else base.MCP.get(real)
    before = all_ts(cwd) if task == "T2" else None
    # T1은 읽기만(쓰기 막음), T2는 고쳐야 하므로 막지 않음. 같은 묶음 안에서는 값이 같게 T1·T2를 따로 돌린다.
    v1.DENIED = "PowerShell,WebFetch,WebSearch,Write,Edit" if task != "T2" else "PowerShell,WebFetch,WebSearch"
    t = v1.run_turn(cwd, {}, (ASK if cname == "serenaask" else "") + {"T1": T1_PROMPT, "T2": T2_PROMPT, "T3": T3_PROMPT}[task], key, 1)
    text = t.get("result") or "\n".join(t["texts"][-2:])
    calls, reads = tool_stats(os.path.join(OUT, f"{key}_t1.jsonl"))
    u = v1.tokens(t["usage"])
    rec = dict(task=task, condition=cname, rep=int(rep), sec=t["sec"], rc=t["rc"], turns=t["turns"],
               tokens=u["input"] + u["cache_create"] + u["cache_read"] + u["output"], usage=u, calls=calls, reads=reads,
               denied=t["denied"], result=text[-2500:])
    if task in ("T1", "T3"):
        found = [k for k in T1_KEYS if re.search(r"\b" + k + r"\b", text)]
        rec.update(found=found, score=len(found))
        msg = f"{len(found)}/6"
    else:
        rec["grade"] = grade_t2(before, all_ts(cwd))
        rec["score"] = rec["grade"]["score"]
        msg = f"{rec['score']}/4 (쓰는 파일 {rec['grade']['callers_done']}/{rec['grade']['callers_total']}, 함정 그대로 {rec['grade']['traps_untouched']})"
        shutil.rmtree(cwd, ignore_errors=True)  # 복사본은 채점 뒤 지움(용량)
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: {msg}  토큰 {rec['tokens']:,}  {t['sec']:.0f}초  도구 {calls}  (전용 도구 {own_calls(calls)}번)"


def score():
    for task in ("T1", "T2", "T3"):
        print(f"== {task}")
        for cname in CONDS:
            rs = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(OUT, f"{task}_{cname}_?.json")))]
            if not rs:
                continue
            n = len(rs)
            print(f"[{cname}] 점수 {[r['score'] for r in rs]}  평균 토큰 {sum(r['tokens'] for r in rs) // n:,}  평균 {sum(r['sec'] for r in rs) / n:.0f}초"
                  f"  새 토큰(캐시 읽기 뺌) {sum(r['usage']['input'] + r['usage']['cache_create'] + r['usage']['output'] for r in rs) // n:,}"
                  f"  읽은 파일 {[r['reads'] for r in rs]}  전용 도구 호출 {[own_calls(r['calls']) for r in rs]}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        keys = sys.argv[2:] or [f"{t}_{c}_{r}" for t in ("T1", "T2") for r in range(1, 4) for c in CONDS]
        with ThreadPoolExecutor(max_workers=2) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
