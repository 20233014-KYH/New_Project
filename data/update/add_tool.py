"""새 도구 넣기: 저장소 하나를 카탈로그에 넣을 준비를 하고, 기존 도구 전부와의 판정을 AI 두 개로 만든다.
- GitHub에서 이름·설명·라이선스·별·최신 릴리스·README 앞부분을 읽는다(gh CLI, 읽기만).
- 판정: judgment/2026-11-21-cross-ai의 같은 지시문으로 Claude(sonnet)·Codex가 따로 판정 → 같은 규칙으로 합침
  (같으면 AI 추정, 다르면 보수적으로, 겹침은 처음 읽는 양 1,000토큰 기준인데 새 도구는 아직 안 재서 상황따라로 낮아짐)
- 기본은 미리보기: data/update/new_<id>/ 에 entry·판정·확인필요만 쓴다. --write를 붙여야 카탈로그(entries·desc_en·compat 두 벌)에 넣는다.
- 한국어 소개·처음 읽는 양·역할 범위는 비워 둔다(화면은 영어 원문과 '측정 안 함'으로 보여 줌). 사람이 채운다.
사용: python data/update/add_tool.py owner/repo 분야번호 [--id 아이디] [--write]
"""
import datetime, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JUDGE = os.path.join(ROOT, "judgment", "2026-11-21-cross-ai", "code")
sys.path.insert(0, JUDGE)
import build_input as BI   # 도구 정보(profile)·기능 목록
import run_judge as RJ     # 지시문·판정자 호출·결과 검사

D = os.path.join(ROOT, "web", "app", "src", "data")
S = os.path.join(ROOT, "server", "sample-data")
TODAY = datetime.date.today().isoformat()
KO = {"overlap": "겹침", "situational": "상황따라", "complement": "보완", "none": "관계 없음"}

def gh(path, raw=False):
    cmd = ["gh", "api", path] + (["-H", "Accept: application/vnd.github.raw"] if raw else [])
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return None
    return r.stdout if raw else json.loads(r.stdout)

def load(p):
    return json.load(open(p, encoding="utf-8"))

def save(p, d):
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def main():
    repo, cat = sys.argv[1], int(sys.argv[2])
    info = gh(f"repos/{repo}")
    if not info:
        sys.exit(f"저장소를 못 읽었어요: {repo}")
    tid = sys.argv[sys.argv.index("--id") + 1] if "--id" in sys.argv else info["name"].lower()
    entries = load(os.path.join(D, "entries.json"))
    if any(e["id"] == tid or e["repo"].lower() == info["full_name"].lower() for e in entries["entries"]):
        sys.exit(f"이미 카탈로그에 있어요: {tid}")
    tag, published = RJ_latest(repo)
    readme = (gh(f"repos/{repo}/readme", raw=True) or "")
    readme = re.sub(r"<[^>]+>|!\[[^\]]*\]\([^)]*\)", "", readme)[:3000]
    entry = {"id": tid, "repo": info["full_name"], "aliases": [], "name": info["name"], "category": cat,
             "summary_ko": None, "role_summary": None, "install_basis": None, "version": tag, "checked_at": None,
             "scope": None, "always_on_tokens_est": None, "token_effect": None, "token_note": "아직 재지 않음",
             "install": None, "cautions": None, "reviews": [],
             "auto": {"stars": info.get("stargazers_count"), "pushed_at": info.get("pushed_at"),
                      "license": (info.get("license") or {}).get("spdx_id"), "open_issues": info.get("open_issues_count"),
                      "latest_release": tag, "latest_release_at": published, "refreshed_at": TODAY},
             "added_at": TODAY, "added_by": "data/update/add_tool.py"}
    out = os.path.join(os.path.dirname(__file__), f"new_{tid}")
    os.makedirs(out, exist_ok=True)

    # 판정: 새 도구 × 기존 도구 전부 (한 묶음)
    new_profile = {"id": tid, "분야": BI.CATS[cat], "설명(원문)": info.get("description"), "한국어 소개": None,
                   "역할 범위": None, "처음 읽는 양(토큰)": None, "기능 목록": [], "README 앞부분": readme}
    others = entries["entries"]
    batch = {"batch": f"new_{tid}", "tools": [new_profile] + [BI.profile(e) for e in others],
             "pairs": [{"a": tid, "b": e["id"], "비슷한 기능 후보": "새 도구라 계산 안 함"} for e in others]}
    save(os.path.join(out, "batch.json"), batch)
    prompt = RJ.prompt(batch)

    def run(judge):
        text, usage = (RJ.run_claude if judge == "claude" else RJ.run_codex)(prompt)
        return judge, RJ.parse(text, batch), usage
    with ThreadPoolExecutor(2) as ex:
        res = {j: (p, u) for j, p, u in ex.map(run, ["claude", "codex"])}
    save(os.path.join(out, "judge_raw.json"), {j: {"usage": u, "pairs": p} for j, (p, u) in res.items()})

    C = {(p["a"], p["b"]): p for p in res["claude"][0]}
    X = {(p["a"], p["b"]): p for p in res["codex"][0]}
    pairs, review = [], []
    for k in C:
        c, x = C[k], X[k]
        if c["relation"] == x["relation"]:
            rel, reason = c["relation"], f"[AI 추정·Claude·Codex 같은 판정 {TODAY}] {c['reason_ko']}"
        else:
            rel = "situational" if {c["relation"], x["relation"]} & {"overlap", "situational"} else "none"
            reason = (f"[AI 추정·두 AI 의견 다름 {TODAY}: Claude {KO[c['relation']]} / Codex {KO[x['relation']]}] "
                      f"Claude: {c['reason_ko']} / Codex: {x['reason_ko']}")
        if rel == "overlap":   # 새 도구는 처음 읽는 양을 아직 안 재서 겹침 기준(둘 다 1,000토큰 이상)을 확인할 수 없음
            rel = "situational"
            reason += " [겹침 기준 적용: 새 도구의 처음 읽는 양을 아직 안 재서 상황따라로 낮춤]"
        if c["relation"] != x["relation"] or "low" in (c.get("confidence"), x.get("confidence")) or "overlap" in (c["relation"], x["relation"]):
            review.append({"b": k[1], "claude": KO[c["relation"]], "codex": KO[x["relation"]], "넣은 판정": KO[rel],
                           "claude_reason": c["reason_ko"], "codex_reason": x["reason_ko"]})
        pairs.append({"a": k[0], "b": k[1], "relation": rel, "reason_ko": reason,
                      "evidence": [{"claim": reason, "type": "ai", "checked_at": TODAY,
                                    "source": "judgment/2026-11-21-cross-ai/판정지시문.md (Claude sonnet·Codex 교차, add_tool.py)"}],
                      "a_version": tag, "b_version": next(e.get("version") for e in others if e["id"] == k[1]),
                      "judged_at": TODAY, "criteria_version": "v2-cross-ai-overlap-1000", "review_state": "ai_estimate"})
    save(os.path.join(out, "entry.json"), entry)
    save(os.path.join(out, "pairs.json"), pairs)
    save(os.path.join(out, "확인필요.json"), review)
    from collections import Counter
    print(f"{tid}: 판정 {len(pairs)}쌍 {dict(Counter(KO[p['relation']] for p in pairs))}, 확인필요 {len(review)} → {out}")
    for r in review[:10]:
        print(f"  - {r['b']}: Claude {r['claude']} / Codex {r['codex']} → {r['넣은 판정']}")

    if "--write" in sys.argv:
        for base in (D, S):
            ep = os.path.join(base, "entries.json")
            d = load(ep); d["entries"].append(entry); save(ep, d)
            cp = os.path.join(base, "compat.json")
            d = load(cp); d["pairs"] += pairs; save(cp, d)
        dp = os.path.join(D, "desc_en.json")
        d = load(dp); d["desc"][tid] = info.get("description") or ""; save(dp, d)
        print("카탈로그에 넣었어요. 한국어 소개(cards_ko.json)·처음 읽는 양은 사람이 채워 주세요.")

def RJ_latest(repo):
    rel = gh(f"repos/{repo}/releases/latest")
    if rel and rel.get("tag_name"):
        return rel["tag_name"], (rel.get("published_at") or "")[:10]
    tags = gh(f"repos/{repo}/tags?per_page=1")
    return (tags[0]["name"], None) if tags else (None, None)

if __name__ == "__main__":
    main()
