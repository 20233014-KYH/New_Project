import json, sys
from pathlib import Path
rows = json.load(open(Path(__file__).parent / "compare_rows.json", encoding="utf-8"))
dest = sys.argv[1]
L = []
L.append("# 36개 도구 비교 축 v0 (읽기용)\n")
L.append("원본 데이터는 [`compare_axes_v0.csv`](compare_axes_v0.csv)입니다. 이 문서는 그 표를 분야별로 풀어 쓴 것입니다.\n")
L.append("- 조사일: 2026-11-09. 저장소별 확인 커밋은 CSV의 `확인커밋`·`커밋날짜` 칸에 있습니다.")
L.append("- 양식: PR #13 `judgment/recommendation/axes_v0.md`의 \"준서 님께 받고 싶은 양식\" + 김용현 요청 \"이럴 때\" 칸 + 노형원 요청 \"실행 방식\" 칸 (PR #12·#16 댓글).")
L.append("- 근거: `calc` 정확히 셈 / `doc` 문서·제작자 주장 / `tested` 팀이 직접 시험 / `ai` 우리가 정리한 비교·추정 / `pattern` 프로그램이 글자 패턴으로 찾음(사람 확인 전).")
L.append("- \"다른 점\"·\"이럴 때\"·\"약한 점\"은 원문 사실을 보고 우리가 정리한 비교라 근거가 `ai`입니다. **모든 줄이 사람 확인 전**입니다.")
L.append("- \"처음 읽는 양\"은 팀 실측(도구 없이 쓸 때보다 첫 응답에서 늘어난 토큰)이고, 작업 중 비용(쓸 때마다 도는 훅, MCP 호출 결과)은 들어 있지 않습니다.")
L.append("- 안전·위험을 판정하지 않습니다. 접근 범위의 \"못 찾음\"은 \"없음\"이 아닙니다.\n")
L.append("## 우선 16개 (하나만 골라야 하는 그룹, PR #15)\n")
L.append("| 그룹 | 도구 | 이럴 때 | 실행 방식 | 처음 읽는 양 |")
L.append("|---|---|---|---|---:|")
for r in rows:
    if r["우선그룹"]:
        L.append(f"| {r['우선그룹']} | {r['도구']} | {r['이럴때']} | {r['실행방식']} | {r['처음읽는양_도구없음대비']} |")
L.append("")
cats = []
for r in rows:
    if r["분야"] not in cats: cats.append(r["분야"])
for cat in sorted(cats):
    rs = [r for r in rows if r["분야"] == cat]
    L.append(f"## {cat}\n")
    names = [rs[0][f"축{i}_이름"] for i in range(1, 5)]
    L.append("| 도구 | " + " | ".join(names) + " |")
    L.append("|---|" + "---|" * 4)
    for r in rs:
        cells = [f"{r[f'축{i}_값']} `{r[f'축{i}_근거']}`".replace("|", "/") for i in range(1, 5)]
        L.append(f"| {r['도구']} | " + " | ".join(cells) + " |")
    L.append("")
    for r in rs:
        L.append(f"### {r['도구']}" + (f" · 우선 그룹: {r['우선그룹']}" if r["우선그룹"] else ""))
        L.append(f"- **다른 점**: {r['다른점']}")
        L.append(f"- **이럴 때**: {r['이럴때']}")
        L.append(f"- **약한 점**: {r['약한점']}")
        L.append(f"- **실행 방식**: {r['실행방식']} `{r['실행방식_근거']}`")
        L.append(f"- **비용**: 라이선스 {r['라이선스']} · 처음 읽는 양 {r['처음읽는양_도구없음대비']} · {r['설치조건_추가비용']}")
        L.append(f"- **접근 범위**: {r['접근범위']}")
        L.append(f"- 버전 {r['버전']} · 커밋 {r['확인커밋']}({r['커밋날짜']}) · 출처: {r['출처']}" + (f" · 확인 안 됨: {r['확인안됨']}" if r["확인안됨"] else ""))
        L.append("")
open(dest, "w", encoding="utf-8").write("\n".join(L))
print(len(L))
