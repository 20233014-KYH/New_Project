"""rows_g1~g6 + 팀 실측 + 접근 범위 표 → compare_axes_v0.csv / compare_axes_v0.md"""
import csv, json, sys, importlib.util
from pathlib import Path
HERE = Path(__file__).parent
PROJ = Path(sys.argv[1]); OUT4 = Path(sys.argv[2]); DEST = Path(sys.argv[3])

AXES = {
 "1 기획·작업 방식": ["만들어 주는 결과물", "정해 주는 작업 단계", "따르게 하는 방식", "세션이 끊겨도 이어지나"],
 "2 토큰·컨텍스트": ["줄이는 대상", "줄이는 양", "줄여도 결과·절차가 같은가", "환경 조건"],
 "3 코드 이해·검색": ["다루는 대상", "찾는 방식", "편집까지 하나", "준비 비용"],
 "4 디자인·프론트엔드": ["측정 가능한 항목", "도구가 겨냥하는 것", "Figma 연결 방향", "사람이 봐야 하는 항목"],
 "5 백엔드·인프라": ["지원하는 대상", "읽기 전용 지원", "접근 범위", "연결 조건"],
 "6 QA·테스트": ["점검 종류", "자동 수정", "실행되는 곳", "깊이"],
}
CAT_OF_FILE = dict(zip([f"rows_g{i}.py" for i in range(1, 7)], AXES))
LICENSE = {
 "rtk-ai/rtk": "Apache-2.0(저장소). 기본 배포판은 Apache-2.0 + BUSL-1.1",
 "oraios/serena": "GPL-3.0-or-later(본체) + MIT(SolidLSP)",
 "trailofbits/skills": "CC BY-SA 4.0",
 "hashicorp/terraform-mcp-server": "MPL-2.0",
}
APACHE = {"ChromeDevTools/chrome-devtools-mcp", "Graphify-Labs/graphify", "JuliusBrussee/caveman", "alibaba/open-code-review",
          "containers/kubernetes-mcp-server", "googleapis/mcp-toolbox", "headroomlabs-ai/headroom", "microsoft/playwright-mcp",
          "pbakaus/impeccable", "supabase/mcp", "thedotmack/claude-mem"}
VERSION = {
 "googleapis/mcp-toolbox": "1.15.0 (cmd/version.txt)", "hashicorp/terraform-mcp-server": "1.4.1 (version/VERSION)",
 "supabase/mcp": "0.16.1 (mcp-server-supabase)", "phuryn/pm-skills": "2.3.0 (marketplace.json)",
 "alibaba/open-code-review": "확인 안 됨 (package.json 0.0.0)",
}
ACCESS_SHORT = {"찾음": "찾음", "검사에서 찾지 못함": "못 찾음", "검사 전": "검사 전", "해당 없음(MCP 도구 없음)": "해당 없음"}

rows = []
for fname, cat in CAT_OF_FILE.items():
    spec = importlib.util.spec_from_file_location(fname[:-3], HERE / fname); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    for r in mod.ROWS:
        rows.append(dict(r, cat=cat))

meas = {r["도구"]: r for r in csv.DictReader(open(PROJ / "judgment/review/2026-10-18-measure36/measured_36.csv", encoding="utf-8-sig"))}
acc = {t["name"]: t for t in json.load(open(OUT4 / "access_scope.json", encoding="utf-8"))["tools"]}
repos = Path(sys.argv[4])

def version_of(repo):
    if repo in VERSION: return VERSION[repo]
    d = repos / repo.replace("/", "_")
    for f in [".claude-plugin/plugin.json", "package.json"]:
        try:
            v = json.load(open(d / f)).get("version")
            if v and v != "0.0.0": return f"{v} ({f})"
        except Exception: pass
    for f in ["pyproject.toml", "Cargo.toml"]:
        try:
            for ln in open(d / f):
                if ln.startswith("version"): return ln.split("=")[1].strip().strip('"') + f" ({f})"
        except Exception: pass
    return "확인 안 됨 (커밋 기준)"

def license_of(repo):
    if repo in LICENSE: return LICENSE[repo]
    return "Apache-2.0" if repo in APACHE else "MIT"

out = []
for r in rows:
    repo = r["repo"]; m = meas.get(repo, {}); a = acc[repo]; names = AXES[r["cat"]]
    assert len(r["axes"]) == 4, repo
    ag = m.get("에이전트수", "")
    rec = {
        "분야": r["cat"], "우선그룹": r["group"] or "", "도구": repo, "저장소": f"https://github.com/{repo}",
        "버전": version_of(repo), "확인커밋": a["checked"].get("commit", ""), "확인일": "2026-11-09" if a["checked"].get("date", "") else "",
        "커밋날짜": a["checked"].get("date", ""), "라이선스": license_of(repo),
    }
    for i, (val, ev) in enumerate(r["axes"], 1):
        rec[f"축{i}_이름"] = names[i - 1]; rec[f"축{i}_값"] = val; rec[f"축{i}_근거"] = ev
    rec.update({
        "실행방식": r["run_mode"], "실행방식_근거": r["run_mode_ev"],
        "다른점": r["diff"], "이럴때": r["when"], "약한점": r["weak"], "비교_근거": "ai",
        "처음읽는양_도구없음대비": m.get("도구없음대비(2회차)", "") or "실측 없음",
        "더해진_스킬": m.get("더해진스킬수", ""), "더해진_명령": m.get("더해진명령수", ""),
        "더해진_에이전트": (str(int(ag) - 6) if ag.strip().isdigit() else ""), "MCP도구": m.get("MCP도구수", ""),
        "첫응답_실행된훅": m.get("실행된훅", ""),
        "설치조건_추가비용": r["install"],
        "접근범위": " / ".join(f"{c}:{ACCESS_SHORT[cell['status']]}" for c, cell in a["cells"].items()),
        "출처": r["sources"], "확인안됨": r["unverified"], "사람확인": "전",
    })
    out.append(rec)

prio = {"절차 전체": 1, "코드 그래프": 2, "디자인 지침": 3, "Figma": 4, "범용 DB": 5, "쿠버네티스": 6}
out.sort(key=lambda x: (0 if x["우선그룹"] else 1, prio.get(x["우선그룹"], 9), x["분야"]))
with open(DEST / "compare_axes_v0.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print(len(out), "rows;", sum(1 for x in out if x["우선그룹"]), "priority")
json.dump(out, open(HERE / "compare_rows.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
