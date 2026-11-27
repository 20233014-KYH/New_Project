"""다시 스캔하지 않고, 이미 만든 접근 범위 표에 사람 검수(reviews.csv)만 반영한다.

사용: python3 apply_reviews.py ../results/2026-11-09
"""
import json, sys
from pathlib import Path
import reviews

res = Path(sys.argv[1])
out = json.load(open(res / "access_scope.json", encoding="utf-8"))
applied, missing, not_ok = reviews.apply(out, reviews.load(Path(__file__).parent.parent / "reviews.csv"))
out["reviewed_count"] = applied
out["note"] = "도움말이며 보증이 아님. 찾지 못함은 없음이 아니다. reviewed=false는 사람 검수 전, true는 사람이 원문과 대조해 맞다고 확인함(reviewed_by·reviewed_at)."
json.dump(out, open(res / "access_scope.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(res / "access_scope.md", "w", encoding="utf-8").write(reviews.render_md(out, out["columns"]))
print(f"반영 {applied}줄 · 표에서 못 찾은 검수 줄 {len(missing)} · 맞음이 아닌 줄 {len(not_ok)}")
for r in missing:
    print("  못 찾음:", r["tool"], r["column"], r["text"][:60])
