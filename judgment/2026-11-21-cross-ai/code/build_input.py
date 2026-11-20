"""다른 분야끼리 540쌍 판정 입력 만들기.
- 도구 정보: entries.json(역할 범위·처음 읽는 양) + desc_en.json + cards_ko.json + features.json(스킬·명령·MCP 도구 설명)
- 비슷한 기능 후보: 같은 분야 90쌍 때와 같은 방식(기능 설명 TF-IDF 코사인 상위 3)
- 묶음: 분야 짝(15개)마다 하나 → batches/c{i}_{j}.json
"""
import json, math, os, re, itertools
from collections import Counter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _find_root(d):
    # 저장소 뿌리(web/app/src/data가 있는 곳)를 위로 올라가며 찾는다(저장소 안·밖 어디서 돌려도 되게)
    while d and not os.path.isdir(os.path.join(d, "web", "app", "src", "data")):
        if os.path.isdir(os.path.join(d, "New_Project", "web")):
            return os.path.join(d, "New_Project")
        d = os.path.dirname(d) if os.path.dirname(d) != d else None
    return d
NP = _find_root(HERE)
D = os.path.join(NP, "web", "app", "src", "data")
entries = json.load(open(os.path.join(D, "entries.json"), encoding="utf-8"))["entries"]
desc = json.load(open(os.path.join(D, "desc_en.json"), encoding="utf-8"))["desc"]
cards = json.load(open(os.path.join(D, "cards_ko.json"), encoding="utf-8"))["cards"]
feats_all = json.load(open(os.path.join(NP, "judgment", "review", "2026-10-18-measure36", "features.json"), encoding="utf-8"))
CATS = {1: "기획·작업 방식", 2: "토큰·컨텍스트", 3: "코드 이해·검색", 4: "디자인·프론트엔드", 5: "백엔드·인프라", 6: "테스트·보안·리뷰"}

STOP = set("the a an and or of to for in on with your you that this it is are be as by from at into any all can use using more not has have one its their via per than when before after skill skills tool tools mcp server claude code user users file files run".split())
def tok(s):
    return [w for w in re.findall(r"[a-z][a-z0-9]{2,}", s.lower().replace("_", " ").replace("-", " ")) if w not in STOP]

feats = {e["id"]: (feats_all.get(e["repo"]) or {}) for e in entries}
docs = {(t, n): tok(n + " " + (d or "")) for t, f in feats.items() for n, d in f.items()}
N = max(len(docs), 1)
df = Counter(w for t in docs.values() for w in set(t))
def vec(t):
    c = Counter(t)
    v = {w: (1 + math.log(n)) * math.log((N + 1) / (df[w] + 1)) for w, n in c.items()}
    nrm = math.sqrt(sum(x * x for x in v.values())) or 1
    return {w: x / nrm for w, x in v.items()}
V = {k: vec(t) for k, t in docs.items()}
cos = lambda x, y: sum(p * y.get(w, 0) for w, p in x.items())

def profile(e):
    f = feats[e["id"]]
    items = list(f.items())
    if len(items) > 40:   # 기능이 아주 많은 묶음(ecc 441개 등)은 이름만 앞 80개
        flist = [n for n, _ in items[:80]] + [f"... 외 {len(items) - 80}개"] if len(items) > 80 else [n for n, _ in items]
    else:
        flist = [f"{n}: {(d or '')[:90]}" for n, d in items]
    c = cards.get(e["id"]) or {}
    return {"id": e["id"], "분야": CATS[e["category"]], "설명(원문)": desc.get(e["id"]),
            "한국어 소개": c.get("summary_ko"), "이럴 때": c.get("when_ko"),
            "역할 범위": e.get("scope"), "처음 읽는 양(토큰)": e.get("always_on_tokens_est"), "기능 목록": flist}

if __name__ == "__main__":
    by_cat = {}
    for e in entries:
        by_cat.setdefault(e["category"], []).append(e)
    total = 0
    for ci, cj in itertools.combinations(sorted(by_cat), 2):
        pairs = []
        for x in by_cat[ci]:
            for y in by_cat[cj]:
                fx, fy = feats[x["id"]], feats[y["id"]]
                m = sorted(((cos(V[(x["id"], a)], V[(y["id"], b)]), a, b) for a in fx for b in fy), reverse=True)[:3]
                pairs.append({"a": x["id"], "b": y["id"],
                              "비슷한 기능 후보": " | ".join(f"{a} ~ {b} ({s:.2f})" for s, a, b in m if s > 0.1) or "없음"})
        tools = [profile(e) for e in by_cat[ci] + by_cat[cj]]
        json.dump({"batch": f"c{ci}_{cj}", "tools": tools, "pairs": pairs},
                  open(os.path.join(HERE, "batches", f"c{ci}_{cj}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        total += len(pairs)
    print("쌍", total, "묶음", len(list(itertools.combinations(sorted(by_cat), 2))))
