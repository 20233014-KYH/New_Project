"""다시 잰 결과(json)를 measured.csv 한 장으로 모은다.
사용: python build_csv.py <measure36 결과 폴더> <4개 버전 비교 결과 폴더>
"""
import csv, json, os, sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NP = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
R36, R4 = sys.argv[1], sys.argv[2]
entries = json.load(open(os.path.join(NP, "web", "app", "src", "data", "entries.json"), encoding="utf-8"))["entries"]


def two(d, name):
    return [json.load(open(os.path.join(d, f"{name}_{r}.json"), encoding="utf-8")) for r in (1, 2)]


base_runs = two(R36, "_none") + two(R36, "_none_end")
base = round(sum(x["context_in_tokens"] for x in base_runs) / 4)
rows = []
for e in entries:
    name = e["repo"].replace("/", "__")
    if not os.path.exists(os.path.join(R36, f"{name}_1.json")):
        rows.append([e["id"], e["version"], e["always_on_tokens_est"], "", "", "", "실측 안 함(10/18과 같은 이유)"])
        continue
    a, b = two(R36, name)
    new = round((a["context_in_tokens"] + b["context_in_tokens"]) / 2) - base
    rows.append([e["id"], e["version"], e["always_on_tokens_est"], a["context_in_tokens"], b["context_in_tokens"], new,
                 f"스킬 {b['skills_count']} 명령 {b['slash_commands_count']} MCP도구 {len(b['mcp_tools'])}"])
with open(os.path.join(HERE, "measured.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "잰 버전", "10/18 값(CC 2.1.191)", "1회차 전체", "2회차 전체", "11/21 값(CC 2.1.318, 도구 없음 대비)", "불러온 것(도구 없음 포함)"])
    w.writerows(rows)
    w.writerow(["_도구 없음", "", 19138, base_runs[0]["context_in_tokens"], base_runs[1]["context_in_tokens"], base, "처음·끝 2번씩 평균"])

ver = []
for tid in ["superpowers", "caveman", "pm-skills", "planning-with-files"]:
    n = two(R4, tid)
    o = two(R4, "old_" + tid)
    b4 = two(R4, "_none") + two(R4, "_none_end")
    bb = sum(x["context_in_tokens"] for x in b4) / 4
    ver.append([tid, round(sum(x["context_in_tokens"] for x in o) / 2 - bb), round(sum(x["context_in_tokens"] for x in n) / 2 - bb),
                f"{o[1]['skills_count']}/{o[1]['slash_commands_count']}", f"{n[1]['skills_count']}/{n[1]['slash_commands_count']}"])
with open(os.path.join(HERE, "versions4.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "옛 버전 값", "최신판 값", "옛 스킬/명령", "최신 스킬/명령"])
    w.writerows(ver)
print("도구 없음", base, "| 도구", len(rows))
for r in ver:
    print(r)
