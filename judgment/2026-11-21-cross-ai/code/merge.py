"""두 AI(Claude sonnet·Codex) 판정을 합쳐 compat.json(화면·서버 두 벌)에 다른 분야 540쌍을 더한다.
- 둘이 같으면 그 판정(AI 추정)
- 둘이 다르면: 한쪽이라도 겹침·상황따라면 '상황따라'(빼기 추천은 하지 않되 알려 줌), 아니면 '관계 없음'(보완은 둘 다 동의할 때만)
- 겹침은 같은 분야 때와 같은 기준: 두 도구 모두 처음 읽는 양 1,000토큰 이상일 때만, 아니면 상황따라로 낮춤
- 직접 시험 기록이 있는 쌍(caveman × superpowers)은 시험 결과로 넣음
- 확인필요.csv: 두 AI 의견이 다르거나 한쪽이라도 확신 낮음
사용: python merge.py [--write]   (--write 없으면 통계·확인필요.csv만)
"""
import csv, glob, json, os, sys
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
COMPATS = [os.path.join(NP, "web", "app", "src", "data", "compat.json"), os.path.join(NP, "server", "sample-data", "compat.json")]
DATE = "2026-11-21"
KO = {"overlap": "겹침", "situational": "상황따라", "complement": "보완", "none": "관계 없음"}
entries = {e["id"]: e for e in json.load(open(os.path.join(NP, "web", "app", "src", "data", "entries.json"), encoding="utf-8"))["entries"]}

def load(judge):
    out = {}
    for f in glob.glob(os.path.join(HERE, "out", judge, "*.json")):
        for p in json.load(open(f, encoding="utf-8"))["pairs"]:
            out[(p["a"], p["b"])] = p
    return out

C, X = load("claude"), load("codex")
keys = sorted(set(C) & set(X))
missing = sorted((set(C) | set(X)) - set(keys))
print("두 AI 모두 판정", len(keys), "한쪽만", len(missing))

TESTED = {frozenset(["caveman", "superpowers"]): dict(
    relation="situational",
    reason="[직접 시험 2026-10-18] 같이 켜고 버그를 고치게 했더니 superpowers 디버깅 절차를 3번 중 3번 건너뛰었어요(caveman 없이는 3번 다 불렀어요). 건너뛴 이유는 확인하지 않았어요.",
    source="judgment/experiments/2026-10-18-statusline-caveman-rtk")}

pairs, review, stat = [], [], Counter()
for k in keys:
    c, x = C[k], X[k]
    a, b = k
    t = TESTED.get(frozenset(k))
    if t:
        rel, state, reason, src = t["relation"], "tested", t["reason"], t["source"]
        stat["직접 시험"] += 1
    else:
        state, src = "ai_estimate", "judgment/2026-11-21-cross-ai/판정지시문.md (Claude sonnet·Codex 교차)"
        if c["relation"] == x["relation"]:
            rel = c["relation"]
            reason = f"[AI 추정·Claude·Codex 같은 판정 {DATE}] {c['reason_ko']}"
            stat["일치"] += 1
        else:
            rel = "situational" if {c["relation"], x["relation"]} & {"overlap", "situational"} else "none"
            reason = (f"[AI 추정·두 AI 의견 다름 {DATE}: Claude {KO[c['relation']]} / Codex {KO[x['relation']]}] "
                      f"Claude: {c['reason_ko']} / Codex: {x['reason_ko']}")
            stat["다름"] += 1
        if rel == "overlap":
            ta, tb = entries[a].get("always_on_tokens_est"), entries[b].get("always_on_tokens_est")
            if not (isinstance(ta, int) and isinstance(tb, int) and ta >= 1000 and tb >= 1000):
                rel = "situational"
                reason += f" [겹침 기준 적용: 처음 읽는 양 {a} {ta}, {b} {tb} 토큰] → 한쪽이 1,000토큰 미만(또는 모름)이라 상황따라로 낮춤"
        if c["relation"] != x["relation"] or "low" in (c.get("confidence"), x.get("confidence")):
            review.append([a, b, KO[c["relation"]], c.get("confidence"), KO[x["relation"]], x.get("confidence"), KO[rel], c["reason_ko"], x["reason_ko"]])
    stat[KO[rel]] += 1
    pairs.append({"a": a, "b": b, "relation": rel, "reason_ko": reason,
                  "evidence": [{"claim": reason, "type": "tested" if state == "tested" else "ai", "source": src, "checked_at": DATE}],
                  "a_version": entries[a].get("version"), "b_version": entries[b].get("version"),
                  "judged_at": DATE, "criteria_version": "v2-cross-ai-overlap-1000", "review_state": state})

print(dict(stat))
with open(os.path.join(HERE, "확인필요.csv"), "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["도구A", "도구B", "Claude", "Claude 확신", "Codex", "Codex 확신", "넣은 판정", "Claude 이유", "Codex 이유"])
    order = lambda r: (0 if "겹침" in (r[2], r[4]) else 1 if "보완" in (r[2], r[4]) else 2 if r[2] != r[4] else 3)
    w.writerows(sorted(review, key=order))
print("확인필요", len(review))

if "--write" in sys.argv:
    for path in COMPATS:
        d = json.load(open(path, encoding="utf-8"))
        have = {frozenset([p["a"], p["b"]]) for p in d["pairs"]}
        add = [p for p in pairs if frozenset([p["a"], p["b"]]) not in have]
        d["pairs"] += add
        d["_note"] = d["_note"].rstrip() + f" 다른 분야 {len(add)}쌍은 {DATE} AI 추정(Claude·Codex 교차, judgment/2026-11-21-cross-ai/)."
        json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(path, "+", len(add))
