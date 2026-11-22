"""다시 잰 '처음 읽는 양'과 겹침 기준을 카탈로그(화면·서버 두 벌)에 넣는다.

겹침 기준(2026-11-21 형원 확정)
- 기준값 = 도구 없는 빈 세션이 처음 읽는 양의 5%. Claude Code가 바뀌면 빈 세션만 다시 재면 기준이 따라온다.
- 두 도구가 '같은 일을 한다'(same_role)고 판정된 쌍에서, 작은 쪽(= 어느 쪽을 꺼도 최소로 아끼는 양)이 기준값 이상이면 겹침,
  아니면 상황따라. (예전 규칙 '둘 다 1,000 이상'과 계산은 같고 기준값만 바뀜)
- 같은 일 묶음이 3개 이상일 때의 판단(합쳐서 기준을 넘는지)은 추천 로직(api.js·JudgeService)이 도구함마다 한다.

사용: python apply_criteria.py <measured.csv> [--write]   (--write 없으면 바뀌는 것만 보여 줌)
"""
import csv, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
NP = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ENTRIES = [os.path.join(NP, "web", "app", "src", "data", "entries.json"), os.path.join(NP, "server", "sample-data", "entries.json")]
COMPATS = [os.path.join(NP, "web", "app", "src", "data", "compat.json"), os.path.join(NP, "server", "sample-data", "compat.json")]
RATIO = 0.05
DATE = "2026-11-21"
CC = "2.1.318"
WRITE = "--write" in sys.argv

rows = list(csv.reader(open(sys.argv[1], encoding="utf-8-sig")))[1:]
base = int(next(r for r in rows if r[0] == "_도구 없음")[5])
LIMIT = round(base * RATIO)
new = {}
for r in rows:
    if r[0].startswith("_") or r[5] == "":
        continue
    new[r[0]] = int(r[5])
print(f"빈 세션 {base:,}토큰 → 겹침 기준 {LIMIT:,}토큰 (5%)")

TOKEN_NOTE = f"첫 응답 기준 실측({DATE}, Claude Code {CC}, 도구 없음 대비)"
SUFFIX = re.compile(r"\s*\[겹침 기준 적용.*$", re.S)
CALC = re.compile(r"^둘 다 켜면 처음 읽는 양 최대 \+[\d,]+ \(하나씩 잰 값의 합\)$")


def fix_entries(path):
    d = json.load(open(path, encoding="utf-8"))
    for e in d["entries"]:
        if e["id"] not in new:
            continue
        v = new[e["id"]]
        if v < 0:   # tdd-guard: 켜면 오히려 줄어듦. 원인 확인 전이라 0으로 두고 메모
            e["always_on_tokens_est"] = 0
            e["token_note"] = TOKEN_NOTE + f" · 켜니 오히려 {v:,}토큰(원인 확인 안 함) → 0으로 표시"
        else:
            e["always_on_tokens_est"] = v
            e["token_note"] = TOKEN_NOTE
    if WRITE:
        json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {e["id"]: e for e in d["entries"]}


def suffix(a, b, ta, tb):
    show = lambda i, t: f"{i} " + ("아직 안 잼" if t is None else f"+{t:,}")
    head = f" [겹침 기준 적용({DATE}, 빈 세션 {base:,}토큰의 5% = {LIMIT:,}토큰): 처음 읽는 양 {show(a, ta)}, {show(b, tb)}토큰]"
    if ta is not None and tb is not None and min(ta, tb) >= LIMIT:
        return head + f" → 어느 쪽을 꺼도 {min(ta, tb):,}토큰 이상 아껴서 겹침"
    return head + " → 작은 쪽이 기준보다 작아 하나를 꺼도 아끼는 양이 크지 않아서 상황따라로 낮춤(같은 일을 하는 도구라는 사실은 카드에 표시)"


def fix_compat(path, ent):
    d = json.load(open(path, encoding="utf-8"))
    d["criteria"] = {"empty_session_tokens": base, "ratio": RATIO, "overlap_min_tokens": LIMIT,
                     "measured_with": f"Claude Code {CC}", "measured_at": DATE,
                     "rule": "같은 일을 하는 두 도구(same_role)에서 작은 쪽 처음 읽는 양이 overlap_min_tokens 이상이면 겹침, 아니면 상황따라. "
                             "도구함에 같은 일 묶음이 3개 이상이면 '가장 큰 것을 남겨도 아끼는 양(합 - 최댓값)'으로 판단"}
    changed = []
    for p in d["pairs"]:
        a, b = p["a"], p["b"]
        ta, tb = ent[a].get("always_on_tokens_est"), ent[b].get("always_on_tokens_est")
        same = p["relation"] == "overlap" or "[겹침 기준 적용" in (p.get("reason_ko") or "")
        if same:
            p["same_role"] = True
            if p.get("review_state") != "tested":
                rel = "overlap" if (ta is not None and tb is not None and min(ta, tb) >= LIMIT) else "situational"
                if rel != p["relation"]:
                    changed.append((a, b, p["relation"], rel))
                p["relation"] = rel
                p["reason_ko"] = SUFFIX.sub("", p["reason_ko"]) + suffix(a, b, ta, tb)
                p["criteria_version"] = f"v3-overlap-5pct-{LIMIT}"
        for ev in p.get("evidence", []):
            c = ev.get("claim") or ""
            if CALC.match(c) and ta is not None and tb is not None:
                ev["claim"] = f"둘 다 켜면 처음 읽는 양 최대 +{ta + tb:,} (하나씩 잰 값의 합, {DATE} Claude Code {CC})"
            elif same and "[겹침 기준 적용" in c:
                ev["claim"] = SUFFIX.sub("", c) + suffix(a, b, ta, tb)
    if WRITE:
        json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return d, changed


ent = None
for path in ENTRIES:
    ent = fix_entries(path)
for path in COMPATS:
    d, changed = fix_compat(path, ent)
print("같은 일 쌍(same_role)", sum(1 for p in d["pairs"] if p.get("same_role")), "| 겹침", sum(1 for p in d["pairs"] if p["relation"] == "overlap"))
print("판정이 바뀐 쌍:", changed or "없음")
print("저장함" if WRITE else "미리보기(--write 없음)")
