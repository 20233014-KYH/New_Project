"""사람 검수표(검수_맞음/틀림/모름 · 검수_고친판정 · 검수_이유·출처)를 카탈로그 판정(compat.json 두 벌)에 넣는다.
- 맞음: 판정은 그대로, 검토 상태만 '사람 검토'로 바꾸고 검수 이유를 덧붙임
- 틀림: 고친 판정으로 바꾸고 이유를 검수 이유로 바꿈(원래 AI 이유는 근거 칸에 남김)
- 모름·빈칸: 건드리지 않음. 직접 시험한 쌍(tested)도 건드리지 않음
처음 쓴 곳: 다른 분야 540쌍 중 확인필요 158줄을 김용현이 검수(PR #30, judgment/review/2026-11-22-cross-ai-review/검수표_v0.csv)
사용: python apply_review.py <검수표.csv> <출처 표시> [--write]
"""
import csv, json, os, sys

sys.stdout.reconfigure(encoding="utf-8")
NP = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
COMPATS = [os.path.join(NP, "web", "app", "src", "data", "compat.json"), os.path.join(NP, "server", "sample-data", "compat.json")]
REL = {"겹침": "overlap", "상황따라": "situational", "보완": "complement", "관계 없음": "none"}
SRC, WRITE = sys.argv[2], "--write" in sys.argv
rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig")))

for path in COMPATS:
    d = json.load(open(path, encoding="utf-8"))
    pm = {frozenset([p["a"], p["b"]]): p for p in d["pairs"]}
    stat = {"맞음": 0, "틀림": 0, "건너뜀": 0}
    for r in rows:
        ok, why = r["검수_맞음/틀림/모름"].strip(), r["검수_이유·출처"].strip()
        p = pm.get(frozenset([r["도구A"], r["도구B"]]))
        if p is None or ok not in ("맞음", "틀림") or p.get("review_state") == "tested":
            stat["건너뜀"] += 1
            continue
        date = "2026-11-22"
        if ok == "틀림":
            new = REL[r["검수_고친판정"].strip()]
            p["evidence"].append({"claim": f"AI 판정(고치기 전 {p['relation']}): {p['reason_ko']}"[:600], "type": "ai",
                                  "source": "judgment/2026-11-21-cross-ai", "checked_at": "2026-11-21"})
            p["relation"], p["reason_ko"] = new, why
        else:
            p["reason_ko"] = p["reason_ko"] + f" / 사람 검토: {why}"
        p["evidence"].append({"claim": why, "type": "review", "source": SRC, "checked_at": date})
        p["review_state"], p["judged_at"] = "human_review", date
        stat[ok] += 1
    print(os.path.relpath(path, NP), stat)
    if WRITE:
        json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("저장함" if WRITE else "미리보기(--write 없음)")
