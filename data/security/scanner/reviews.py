"""사람 검수 결과(reviews.csv)를 접근 범위 표에 반영하고, 검토용 마크다운을 만든다.

- 검수는 사실 줄 하나 단위: (도구 id, 칸, 문장)이 정확히 같은 줄에만 붙는다. 문장이 바뀌면 다시 확인해야 한다.
- 근거 종류(evidence_code)는 바꾸지 않는다. 사람이 확인하면 reviewed=true와 누가·언제만 더한다(CLAUDE.md "검수 상태는 별도 필드").
- result가 "맞음"인 줄만 reviewed=true. "틀림"은 표에 반영하지 않고 고칠 목록으로만 돌려준다.
- fixed_text 칸이 있으면(사실은 맞지만 읽는 사람이 오해하기 쉬운 문장) 화면 문장을 그걸로 바꾸고,
  프로그램이 만든 원래 문장은 text_raw에 남긴다. 다시 스캔해도 원래 문장(text)으로 찾아서 같은 고침이 붙는다.
"""
import csv
from pathlib import Path

FIELDS = ["tool", "column", "text", "result", "reviewer", "date", "note", "fixed_text"]


def load(path):
    path = Path(path)
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def apply(out, rows):
    """out(access_scope dict)에 검수를 반영. (반영 수, 표에서 못 찾은 줄, 맞음이 아닌 줄)을 돌려준다."""
    idx = {(r["tool"], r["column"], r["text"]): r for r in rows}
    used, applied = set(), 0
    for t in out["tools"]:
        for c, cell in t["cells"].items():
            for x in cell["facts"]:
                key_text = x.get("text_raw", x["text"])
                r = idx.get((t["id"], c, key_text))
                if not r:
                    continue
                used.add((t["id"], c, key_text))
                if r["result"] == "맞음":
                    if (r.get("fixed_text") or "").strip():
                        x["text_raw"] = key_text
                        x["text"] = r["fixed_text"].strip()
                    x["reviewed"] = True
                    x["reviewed_by"] = r["reviewer"]
                    x["reviewed_at"] = r["date"]
                    applied += 1
    missing = [r for k, r in idx.items() if k not in used]
    not_ok = [r for r in rows if r["result"] != "맞음"]
    return applied, missing, not_ok


def evidence_label(x):
    if x.get("reviewed"):
        return x["evidence"].replace("(사람 확인 전)", "") + f" · 사람 확인함({x.get('reviewed_by', '')}, {x.get('reviewed_at', '')})"
    if x["evidence_code"] == "pattern":
        return x["evidence"] + ", 사람 확인 전"
    return x["evidence"]


def render_md(out, cols):
    md = []
    for t in out["tools"]:
        md.append(f"### {t['name']}  (확인: {t['checked'].get('commit','')} · {t['checked'].get('date','')})")
        for c in cols:
            cell = t["cells"][c]
            md.append(f"- **{c}** [{cell['status']}]")
            for x in cell["facts"]:
                md.append(f"    - ({x['when']}) {x['text']} — {evidence_label(x)}"
                          + (f" · {x['confirm']}" if x.get("confirm") and not x.get("reviewed") else ""))
            for n in cell["notes"]:
                md.append(f"    - 참고: {n}")
        md.append("")
    return "\n".join(md)
