#!/usr/bin/env python3
"""측정·검수 결과를 기획안 6-1장 형식(entries.json, compat.json)으로 옮긴 서버용 샘플 데이터를 만든다.

입력
- review/measured_36.csv          : 36개 실측
- probe.json                      : GitHub API로 읽은 버전·별 수·라이선스·최근 업데이트
- results/<도구>_2.json           : 실측 때 불러온 스킬·명령·에이전트·MCP 도구 수
- 플러그인 폴더의 hooks/hooks.json 또는 plugin.json 의 hooks : 훅 개수(시점별)
- 김용현 검수표(pairs_90.csv, KIM 브랜치)  : 관계 판정
출력: sample-data/entries.json, sample-data/compat.json

원칙: 기획안의 필드 이름을 그대로 쓴다. 아직 정하지 않은 값(한 줄 설명, 하는 일, 설치법 등)은 null 로 둔다.
"""
import csv
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = sys.argv[:2]
import measure36 as M  # noqa: E402

PAIRS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "review", "pairs_90.csv")
OUT = os.path.join(HERE, "sample-data")
os.makedirs(OUT, exist_ok=True)
CHECKED = "2026-10-18"
CC_VER = "2.1.191"
probe = {p["id"]: p for p in json.load(open(os.path.join(HERE, "probe.json"), encoding="utf-8"))}
measured = {r["도구"]: r for r in csv.DictReader(open(os.path.join(HERE, "review", "measured_36.csv"), encoding="utf-8-sig"))}
t36 = json.load(open(os.path.join(HERE, "..", "..", "..", "데이터", "점검_잠정36.json"), encoding="utf-8"))


def gh_meta(tid):
    """probe 에 없던 별 수·최근 업데이트·열린 이슈 수는 GitHub API에서 읽는다(읽기만)."""
    import subprocess
    r = subprocess.run(["gh", "api", f"repos/{tid}", "--jq", "{s:.stargazers_count,p:.pushed_at,i:.open_issues_count,l:.license.spdx_id}"],
                       capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout) if r.returncode == 0 else {}


def hook_events(tid):
    ev = {}
    for d in M.TOOLS[tid].get("plugins", []):
        srcs = []
        hj = os.path.join(d, "hooks", "hooks.json")
        if os.path.exists(hj):
            srcs.append(json.load(open(hj, encoding="utf-8")).get("hooks", {}))
        pj = os.path.join(d, ".claude-plugin", "plugin.json")
        if os.path.exists(pj):
            h = json.load(open(pj, encoding="utf-8")).get("hooks")
            if isinstance(h, dict):
                srcs.append(h)
            elif isinstance(h, str) and os.path.exists(os.path.join(d, h)):
                srcs.append(json.load(open(os.path.join(d, h), encoding="utf-8")).get("hooks", {}))
        for s in srcs:
            for event, groups in s.items():
                n = sum(len(g.get("hooks", [])) for g in groups if isinstance(g, dict))
                ev[event] = ev.get(event, 0) + n
    if M.TOOLS[tid].get("hooks"):
        for event, groups in M.TOOLS[tid]["hooks"].items():
            ev[event] = ev.get(event, 0) + sum(len(g.get("hooks", [])) for g in groups)
    return ev


def safe_id(tid):
    owner, name = tid.lower().split("/")
    return f"{owner}-{name}" if name in ("mcp", "skills") else name


entries = []
for t in t36:
    tid = t["id"]
    m = measured.get(tid, {})
    p = probe.get(tid, {})
    spec = M.TOOLS[tid]
    res = os.path.join(HERE, "results", M.safe(tid) + "_2.json")
    r = json.load(open(res, encoding="utf-8")) if os.path.exists(res) else None
    ev = hook_events(tid)
    tok = int(m["도구없음대비(2회차)"]) if m.get("도구없음대비(2회차)") else None
    meta = gh_meta(tid)
    entries.append({
        "id": safe_id(tid),
        "repo": tid,
        "aliases": [p["full"]] if p.get("full") and p["full"] != tid else [],
        "name": tid.split("/")[1],
        "category": int(t["cat"].split(" ")[0]),
        "summary_ko": None,
        "role_summary": None,
        "install_basis": "전체 설치" if len(spec.get("plugins", [])) > 1 else None,
        "version": p.get("release"),
        "checked_at": CHECKED,
        "scope": None if r is None else {
            "skills": int(m["더해진스킬수"] or 0), "agents": max(int(m["에이전트수"] or 0) - 6, 0),
            "commands": int(m["더해진명령수"] or 0), "mcp": len(r["mcp_tools"]),
            "hooks_total": sum(ev.values()), "hook_events": ev,
        },
        "always_on_tokens_est": tok,
        "token_effect": None,
        "token_note": f"첫 응답 기준 실측({CHECKED}, Claude Code {CC_VER}, 도구 없음 대비)" if tok is not None else (m.get("측정") or "확인 안 됨"),
        "install": None,
        "cautions": m.get("메모") or None,
        "reviews": [],
        "auto": {"stars": meta.get("s", t.get("stars")), "pushed_at": meta.get("p", ""), "license": meta.get("l") or t.get("lic"), "open_issues": meta.get("i")},
    })

REL = {"겹침": "overlap", "상황따라": "situational", "보완": "complement", "관계 없음": "none", "고장 확인": "verified_issue"}
TESTED = {frozenset(["obra/superpowers", "affaan-m/ECC"]): "judgment/experiments/2026-10-17-superpowers-ecc",
          frozenset(["JuliusBrussee/caveman", "rtk-ai/rtk"]): "judgment/experiments/2026-10-18-statusline-caveman-rtk",
          frozenset(["JuliusBrussee/caveman", "jarrodwatts/claude-hud"]): "judgment/experiments/2026-10-18-statusline-caveman-rtk"}
ver = {e["repo"]: e["version"] for e in entries}
tok = {e["repo"]: e["always_on_tokens_est"] for e in entries}
compat = []
for row in csv.DictReader(open(PAIRS, encoding="utf-8-sig")):
    a, b = row["도구A"], row["도구B"]
    ok = row.get("검수_맞음/틀림/모름")
    label = row["판정초안"] if ok == "맞음" else (row.get("검수_고친판정") or row["판정초안"])
    reviewed = bool(ok)
    evidence = []
    key = frozenset([a, b])
    if key in TESTED:
        evidence.append({"claim": "같이 켜서 직접 시험함", "type": "tested", "source": TESTED[key], "checked_at": CHECKED})
    evidence.append({"claim": (row.get("검수_이유·출처") or row["이유"])[:300], "type": "doc" if reviewed else ("calc" if row["근거종류"] == "계산" else "doc"),
                     "source": "README·features.json" if reviewed else row["근거종류"], "checked_at": "2026-10-19" if reviewed else CHECKED})
    if tok.get(a) is not None and tok.get(b) is not None:
        evidence.append({"claim": f"둘 다 켜면 처음 읽는 양 최대 +{tok[a] + tok[b]:,} (하나씩 잰 값의 합)", "type": "calc"})
    compat.append({
        "a": safe_id(a), "b": safe_id(b), "relation": REL.get(label, None),
        "reason_ko": (row.get("검수_이유·출처") or row["이유"]),
        "evidence": evidence,
        "a_version": ver.get(a), "b_version": ver.get(b),
        "judged_at": "2026-10-19" if reviewed else CHECKED,
        "criteria_version": "v1-overlap-1000",
        "review_state": "tested" if key in TESTED else ("human_review" if reviewed else "ai_estimate"),
        "needs_review": label not in REL,
    })

json.dump({"_note": "샘플 데이터. 기획안 6-1장 형식. summary_ko·role_summary·install 은 아직 안 씀(null). 토큰은 실측.", "entries": entries},
          open(os.path.join(OUT, "entries.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"_note": "샘플 데이터. 김용현 1차 검수(PR #4) 반영. 겹침 기준 1,000토큰(임시).", "pairs": compat},
          open(os.path.join(OUT, "compat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
print("entries", len(entries), "compat", len(compat), Counter(c["relation"] for c in compat), Counter(c["review_state"] for c in compat))
