#!/usr/bin/env python3
"""36개 실측 결과로 김용현 검수용 자료를 만든다.

1) measured_36.csv : 도구별 처음 읽는 양(2회), 도구 없음 대비, 불러온 스킬·명령·에이전트·MCP 도구 수, 연결 상태, 훅 이상
2) pairs_90.csv    : 같은 분야 안의 모든 쌍(분야당 15쌍). 판정 초안·근거 종류·같이 켰을 때 최대 비용·겹치는 기능 후보·검수 질문
3) features.json   : 도구별 기능 목록(스킬/명령/MCP 도구 이름 + SKILL.md 설명)
판정 초안 규칙(사람이 확인해야 함):
- 시험으로 잰 쌍은 그 결과를 쓴다(근거: 실측).
- 같은 외부 서비스를 다루는 MCP 둘(예: 쿠버네티스 둘, Figma 둘) → 겹침 후보(근거: 문서·계산)
- 기능 설명 유사도가 높음(상위 기능쌍 점수 ≥ 0.45 가 3개 이상) → 겹침 후보(근거: 계산)
- 유사도 중간(≥ 0.30 가 1개 이상) → 상황따라 후보(근거: 계산)
- 그 밖 → 관계 없음 후보(근거: 계산)
"""
import csv
import glob
import itertools
import json
import math
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
OUTD = os.path.join(HERE, "review")
os.makedirs(OUTD, exist_ok=True)
sys.path.insert(0, HERE)
sys.argv = sys.argv[:1]
import measure36 as M  # noqa: E402

TOOLS36 = json.load(open(os.path.join(HERE, "..", "..", "..", "데이터", "점검_잠정36.json"), encoding="utf-8"))
# 기준값: 같은 시간에 함께 잰 '도구 없음'(처음·끝). Claude Code 서버 쪽 설정이 바뀌면 기본 도구 수가 달라지므로 같이 확인한다.
_b = [json.load(open(os.path.join(RES, f"_{n}_{r}.json"), encoding="utf-8")) for n in ("none", "none_end") for r in (1, 2)]
BASE = _b[1]["context_in_tokens"]
BASE_SKILLS = _b[1]["skills_count"]
BASE_CMDS = _b[1]["slash_commands_count"]
BASE_TOOLS = _b[1]["tools_count"]
BASE_ALL = [x["context_in_tokens"] for x in _b]
assert len({x["tools_count"] for x in _b}) == 1 and max(BASE_ALL) - min(BASE_ALL) <= 10, ("기준값이 처음과 끝에서 다름", BASE_ALL)

# 시험으로 직접 잰 쌍
MEASURED = {
    frozenset(["obra/superpowers", "affaan-m/ECC"]): ("overlap", "실측", "27번 시험: 결과 같음, 토큰 약 1.9배·시간 약 1.5배, ECC 겹치는 스킬 0번 사용 (judgment/experiments/2026-10-17-superpowers-ecc)"),
    frozenset(["JuliusBrussee/caveman", "jarrodwatts/claude-hud"]): ("situational", "실측", "상태줄 자리는 하나. claude-hud가 자리를 쓰면 caveman 상태줄 배지는 안 보임(caveman이 알아서 물러남) (judgment/experiments/2026-10-18-statusline-caveman-rtk 결과 1)"),
    frozenset(["JuliusBrussee/caveman", "rtk-ai/rtk"]): ("complement", "실측", "36번 시험: 충돌 없음, 줄이는 곳이 다름(말 / 명령 출력) (judgment/experiments/2026-10-18-statusline-caveman-rtk)"),
}
# 같은 외부 대상을 다루는 MCP (문서 기준)
SAME_TARGET = {
    frozenset(["containers/kubernetes-mcp-server", "Flux159/mcp-server-kubernetes"]): "둘 다 쿠버네티스 클러스터를 다루는 MCP 서버",
    frozenset(["GLips/Figma-Context-MCP", "grab/cursor-talk-to-figma-mcp"]): "둘 다 Figma 디자인을 읽는 MCP 서버(하나는 읽기 위주, 하나는 Figma 플러그인과 연결해 쓰기도 함)",
    frozenset(["microsoft/playwright-mcp", "ChromeDevTools/chrome-devtools-mcp"]): "둘 다 브라우저를 열어 조작하는 MCP 서버",
    frozenset(["Graphify-Labs/graphify", "colbymchenry/codegraph"]): "둘 다 코드를 그래프로 색인해 검색하는 도구",
}


def load(tid):
    a = os.path.join(RES, M.safe(tid) + "_1.json")
    b = os.path.join(RES, M.safe(tid) + "_2.json")
    if not (os.path.exists(a) and os.path.exists(b)):
        return None, None
    return json.load(open(a, encoding="utf-8")), json.load(open(b, encoding="utf-8"))


def skill_descs(tid):
    """불러온 플러그인/프로젝트 폴더의 SKILL.md 와 commands/*.md 에서 이름·설명을 읽는다."""
    roots = list(M.TOOLS[tid].get("plugins", []))
    cwd = os.path.join(M.CWDS, M.safe(tid), ".claude")
    if os.path.isdir(cwd):
        roots.append(cwd)
    out = {}
    for r in roots:
        files = glob.glob(os.path.join(r, "**", "SKILL.md"), recursive=True) + glob.glob(os.path.join(r, "commands", "*.md")) + glob.glob(os.path.join(r, "**", "commands", "*.md"), recursive=True)
        for f in files:
            if "node_modules" in f:
                continue
            txt = open(f, encoding="utf-8", errors="ignore").read()
            m = re.match(r"---\s*\n(.*?)\n---", txt, re.S)
            fm = m.group(1) if m else ""
            nm = re.search(r"^name:\s*(.+)$", fm, re.M)
            ds = re.search(r"^description:\s*(.+?)(?=\n[a-z_-]+:|\Z)", fm, re.M | re.S)
            name = (nm.group(1).strip().strip("\"'") if nm else os.path.basename(os.path.dirname(f)) if f.endswith("SKILL.md") else os.path.splitext(os.path.basename(f))[0])
            out[name] = re.sub(r"\s+", " ", ds.group(1)).strip().strip("\"'>|- ")[:400] if ds else ""
    return out


STOP = set("the a an and or of to for in on with your you that this it is are be as by from at into any all can use using more not has have one its their via per than when before after skill skills tool tools mcp server claude code user users file files run".split())


def tok(s):
    return [w for w in re.findall(r"[a-z][a-z0-9]{2,}", s.lower().replace("_", " ").replace("-", " ")) if w not in STOP]


def main():
    rows, feats = [], {}
    print("기준값(도구 없음)", BASE_ALL, "스킬", BASE_SKILLS, "명령", BASE_CMDS, "도구", BASE_TOOLS)
    for t in TOOLS36:
        tid = t["id"]
        spec = M.TOOLS[tid]
        a, b = load(tid)
        if spec.get("skip") or a is None:
            rows.append({"id": tid, "cat": t["cat"], "status": spec.get("skip") or "측정 결과 없음"})
            feats[tid] = {}
            continue
        ds = skill_descs(tid)
        mcp_names = [x.split("__", 2)[-1] for x in b["mcp_tools"]]
        f = dict(ds)
        for n in mcp_names:
            f.setdefault("mcp:" + n, "")
        feats[tid] = f
        servers = [(s.get("name"), s.get("status")) for s in (b.get("mcp_servers") or [])]
        rows.append({
            "id": tid, "cat": t["cat"], "status": "측정함",
            "tok1": a["context_in_tokens"], "tok2": b["context_in_tokens"], "delta": b["context_in_tokens"] - BASE,
            "skills": b["skills_count"] - BASE_SKILLS, "cmds": b["slash_commands_count"] - BASE_CMDS, "agents": b["agents_count"],
            "mcp_tools": len(b["mcp_tools"]), "servers": "; ".join(f"{n}:{s}" for n, s in servers),
            "hooks": "; ".join(f"{k}x{v}" for k, v in b["hooks_fired"].items()),
            "hooks_bad": len(a["hooks_bad"]) + len(b["hooks_bad"]),
            "note": "; ".join(x for x in [b.get("note", ""),
                                           "MCP 리소스 읽기 도구 3개가 함께 붙음" if b["tools_count"] - len(b["mcp_tools"]) == BASE_TOOLS + 3 else ("기본 도구 수가 기준과 다름(확인 필요)" if b["tools_count"] - len(b["mcp_tools"]) != BASE_TOOLS else ""),
                                           "1·2회차 차이 큼" if abs(a["context_in_tokens"] - b["context_in_tokens"]) > 20 else ""] if x),
        })
    by_id = {r["id"]: r for r in rows}

    with open(os.path.join(OUTD, "measured_36.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["분야", "도구", "측정", "1회차_첫응답입력토큰", "2회차", "도구없음대비(2회차)", "더해진스킬수", "더해진명령수", "에이전트수",
                    "MCP도구수", "MCP연결상태", "실행된훅", "훅이상", "메모"])
        for r in rows:
            w.writerow([r["cat"], r["id"], r["status"], r.get("tok1", ""), r.get("tok2", ""), r.get("delta", ""), r.get("skills", ""), r.get("cmds", ""),
                        r.get("agents", ""), r.get("mcp_tools", ""), r.get("servers", ""), r.get("hooks", ""), r.get("hooks_bad", ""), r.get("note", "")])

    # 기능 유사도 (전체 기능 문서로 IDF)
    docs = {(tid, n): tok(n + " " + d) for tid, f in feats.items() for n, d in f.items()}
    N = max(len(docs), 1)
    df = Counter(w for t in docs.values() for w in set(t))

    def vec(t):
        c = Counter(t)
        v = {w: (1 + math.log(n)) * math.log((N + 1) / (df[w] + 1)) for w, n in c.items()}
        nrm = math.sqrt(sum(x * x for x in v.values())) or 1
        return {w: x / nrm for w, x in v.items()}

    V = {k: vec(t) for k, t in docs.items()}
    cos = lambda x, y: sum(p * y.get(w, 0) for w, p in x.items())

    pairs = []
    cats = sorted({t["cat"] for t in TOOLS36})
    for c in cats:
        ids = [t["id"] for t in TOOLS36 if t["cat"] == c]
        for x, y in itertools.combinations(ids, 2):
            key = frozenset([x, y])
            fx, fy = feats.get(x, {}), feats.get(y, {})
            matches = sorted(((cos(V[(x, a)], V[(y, b)]), a, b) for a in fx for b in fy), reverse=True)[:5]
            hi = sum(1 for s, _, _ in matches if s >= 0.45)
            mid = sum(1 for s, _, _ in matches if s >= 0.30)
            dx, dy = by_id[x].get("delta"), by_id[y].get("delta")
            cost = (dx + dy) if isinstance(dx, int) and isinstance(dy, int) else ""
            if key in MEASURED:
                rel, ev, why = MEASURED[key]
            elif key in SAME_TARGET:
                rel, ev, why = "overlap", "문서", SAME_TARGET[key]
            elif not fx or not fy:
                rel, ev, why = "판정 못 함", "-", "한쪽이 세션에 읽히는 기능이 없거나 측정 못 함 → 문서로 판정 필요"
            elif hi >= 3:
                rel, ev, why = "overlap", "계산", f"기능 설명이 비슷한 쌍이 {hi}개"
            elif mid >= 1:
                rel, ev, why = "situational", "계산", f"기능 설명이 조금 비슷한 쌍이 {mid}개"
            else:
                rel, ev, why = "none", "계산", "비슷한 기능 설명을 못 찾음"
            pairs.append({"cat": c, "a": x, "b": y, "rel": rel, "ev": ev, "why": why, "cost": cost,
                          "top": " | ".join(f"{a} ~ {b} ({s:.2f})" for s, a, b in matches[:3] if s > 0)})

    KO = {"overlap": "겹침", "situational": "상황따라", "complement": "보완", "none": "관계 없음", "verified_issue": "고장 확인"}
    with open(os.path.join(OUTD, "pairs_90.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["번호", "분야", "도구A", "도구B", "판정초안", "근거종류", "이유", "같이켰을때_최대추가토큰(A+B)", "겹치는기능후보(상위3)",
                    "검수_맞음/틀림/모름", "검수_고친판정", "검수_이유·출처"])
        for i, p in enumerate(pairs, 1):
            w.writerow([i, p["cat"], p["a"], p["b"], KO.get(p["rel"], p["rel"]), p["ev"], p["why"], p["cost"], p["top"], "", "", ""])
    json.dump(feats, open(os.path.join(OUTD, "features.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cnt = Counter(KO.get(p["rel"], p["rel"]) for p in pairs)
    print("쌍", len(pairs), dict(cnt))
    for p in pairs:
        print(f"{p['cat'][:6]} {p['a']:<38} x {p['b']:<38} {KO.get(p['rel'], p['rel']):<6} {p['ev']} {p['cost']} | {p['top'][:110]}")


if __name__ == "__main__":
    main()
