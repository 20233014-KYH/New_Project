"""카탈로그 최신화: 36개 도구의 GitHub 정보(별, 최근 업데이트, 라이선스, 열린 이슈, 최신 릴리스)를 다시 읽어
entries.json(화면·서버 두 벌)의 auto 칸을 고친다. 우리가 잰 값(version, scope, 처음 읽는 양)은 건드리지 않는다.
- 측정한 버전과 최신 릴리스가 다르면 '다시 잴 것'으로 보고서에 적는다(판정·토큰을 다시 볼 후보).
- gh CLI(로그인된 GitHub)로 읽기만 한다.
사용: python data/update/refresh.py [--write]
"""
import json, os, re, subprocess, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILES = [os.path.join(ROOT, "web", "app", "src", "data", "entries.json"), os.path.join(ROOT, "server", "sample-data", "entries.json")]
TODAY = datetime.date.today().isoformat()

def gh(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None

def latest(repo):
    rel = gh(f"repos/{repo}/releases/latest")
    if rel and rel.get("tag_name"):
        return rel["tag_name"], (rel.get("published_at") or "")[:10]
    tags = gh(f"repos/{repo}/tags?per_page=1")
    return (tags[0]["name"], None) if tags else (None, None)

def norm(v):
    return (v or "").lower().lstrip("v").split("@")[-1]

def main():
    d = json.load(open(FILES[0], encoding="utf-8"))
    report = []
    for e in d["entries"]:
        info = gh(f"repos/{e['repo']}")
        if not info:
            report.append((e["id"], "저장소를 못 읽음", "", ""))
            continue
        if info.get("full_name", "").lower() != e["repo"].lower():
            report.append((e["id"], f"저장소 이름이 바뀜 → {info.get('full_name')}", "", ""))
        tag, published = latest(e["repo"])
        a = e.setdefault("auto", {})
        old_stars = a.get("stars")
        a.update({"stars": info.get("stargazers_count"), "pushed_at": info.get("pushed_at"),
                  "license": (info.get("license") or {}).get("spdx_id") or a.get("license"),
                  "open_issues": info.get("open_issues_count"), "archived": info.get("archived", False),
                  "latest_release": tag, "latest_release_at": published, "refreshed_at": TODAY})
        if info.get("archived"):
            report.append((e["id"], "보관됨(더 이상 관리 안 함)", "", ""))
        if tag and e.get("version") and norm(tag) != norm(e["version"]):
            shape = lambda v: re.sub(r"[0-9.]", "", v.lower().lstrip("v"))
            if shape(tag) != shape(e["version"]):   # 여러 패키지를 한 저장소에서 내는 경우(태그 앞 이름이 다름)
                report.append((e["id"], "태그 형식이 달라 사람이 확인", e.get("version"), tag))
            else:
                report.append((e["id"], "새 버전 나옴 → 다시 잴 것", e.get("version"), tag))
        print(f"{e['id']:<28} 별 {old_stars} → {a['stars']}  최신 {tag}  (잰 버전 {e.get('version')})")
    print("\n보고:")
    for r in report:
        print(" -", " | ".join(str(x) for x in r if x))
    with open(os.path.join(os.path.dirname(__file__), f"refresh_{TODAY}.md"), "w", encoding="utf-8") as fh:
        fh.write(f"# 카탈로그 최신화 {TODAY}\n\n| 도구 | 내용 | 잰 버전 | 최신 |\n|---|---|---|---|\n")
        for r in report:
            fh.write("| " + " | ".join(str(x) for x in r) + " |\n")
    if "--write" in sys.argv:
        for f in FILES:
            json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            open(f, "a", encoding="utf-8").write("\n")
        print("저장:", FILES)

if __name__ == "__main__":
    main()
