"""새 오픈소스 후보 찾기: GitHub에서 Claude Code 관련 주제(topic)의 인기 저장소 중 카탈로그에 없는 것을 모아
후보 목록(candidates_날짜.csv)으로 낸다. 자동으로 카탈로그에 넣지 않는다(사람이 고른 뒤 add_tool.py).
- 분야는 설명 낱말로 '추정'만 적는다(사람이 확인).
사용: python data/update/discover.py [--min-stars 1000] [--days 90]
"""
import csv, datetime, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TODAY = datetime.date.today()
TOPICS = ["claude-code", "claude-code-plugin", "claude-skills", "claude-code-skills", "mcp-server"]
GUESS = [  # 설명에 이 낱말이 있으면 이 분야로 추정 (위에서부터 먼저 맞는 것)
    (2, ["token", "context window", "compress", "memory", "usage", "cost"]),
    (3, ["codebase", "code search", "semantic", "graph", "documentation", "docs", "symbol"]),
    (4, ["design", "ui", "frontend", "figma", "css", "component"]),
    (5, ["database", "sql", "postgres", "kubernetes", "terraform", "cloud", "aws", "infra", "devops"]),
    (6, ["test", "security", "review", "browser", "playwright", "audit"]),
    (1, ["workflow", "plan", "agent", "skill", "methodology", "spec"]),
]

def arg(name, default):
    return int(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default

def search(topic, min_stars, since):
    q = f"topic:{topic} stars:>={min_stars} pushed:>={since}"
    r = subprocess.run(["gh", "api", "-X", "GET", "search/repositories", "-f", f"q={q}", "-f", "sort=stars", "-f", "per_page=50"],
                       capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout).get("items", []) if r.returncode == 0 else []

def main():
    min_stars, days = arg("--min-stars", 1000), arg("--days", 90)
    since = (TODAY - datetime.timedelta(days=days)).isoformat()
    entries = json.load(open(os.path.join(ROOT, "web", "app", "src", "data", "entries.json"), encoding="utf-8"))["entries"]
    have = {e["repo"].lower() for e in entries}
    found = {}
    for t in TOPICS:
        for it in search(t, min_stars, since):
            name = it["full_name"]
            if name.lower() in have or it.get("archived"):
                continue
            row = found.setdefault(name, {"repo": name, "stars": it["stargazers_count"], "pushed": it["pushed_at"][:10],
                                          "license": (it.get("license") or {}).get("spdx_id") or "", "desc": it.get("description") or "",
                                          "topics": set()})
            row["topics"].add(t)
    # 주제 표시만으로는 관련 없는 저장소도 섞여서(워크플로 플랫폼 등), 설명에 Claude Code 도구다운 낱말이 있는 것을 위로
    hint = lambda r: any(x in r["desc"].lower() for x in ["claude", "skill", "plugin", "mcp", "subagent", "hook"])
    rows = sorted(found.values(), key=lambda r: (not hint(r), -r["stars"]))
    out = os.path.join(os.path.dirname(__file__), f"candidates_{TODAY}.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["저장소", "별", "최근 업데이트", "라이선스", "분야 추정(사람 확인)", "설명에 도구 낱말", "찾은 주제", "설명(원문)"])
        for r in rows:
            low = r["desc"].lower()
            cat = next((c for c, words in GUESS if any(x in low for x in words)), "")
            w.writerow([r["repo"], r["stars"], r["pushed"], r["license"], cat, "O" if hint(r) else "", " ".join(sorted(r["topics"])), r["desc"]])
    print(f"카탈로그에 없는 후보 {len(rows)}개(설명에 도구 낱말 있음 {sum(map(hint, rows))}개) → {out}")
    for r in rows[:15]:
        print(f"  {r['stars']:>7}  {r['repo']}  {r['desc'][:70]}")

if __name__ == "__main__":
    main()
