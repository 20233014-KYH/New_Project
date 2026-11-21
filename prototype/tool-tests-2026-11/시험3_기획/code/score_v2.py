#!/usr/bin/env python3
"""시험 3 v2 자동 채점. AI 채점 없이, 상황마다 미리 정한 항목이 답에 있는지 정해진 규칙으로 확인한다.

- 본 글: 첫·두 번째 대답의 글 + 파일에 쓴 내용(계획 모드처럼 계획을 파일로 남기는 경우)
- 결과: results_v2/_score.csv (실행마다), 화면에 조건별 평균
사용법: python score_v2.py
"""
import csv
import glob
import json
import os
import re
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results_v2")


def written(jsonl):
    """실행 기록에서 Write/Edit로 쓴 내용과 ExitPlanMode 계획을 모은다."""
    out = []
    if not os.path.exists(jsonl):
        return ""
    for line in open(jsonl, encoding="utf-8"):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("type") != "assistant":
            continue
        for c in (e.get("message") or {}).get("content", []):
            if c.get("type") == "tool_use":
                inp = c.get("input") or {}
                out.append(inp.get("content") or inp.get("new_string") or inp.get("plan") or "")
    return "\n".join(out)


def has(pat, text):
    return 1 if re.search(pat, text, re.I | re.S) else 0


def checks(r, key):
    t1, t2 = r["turn1"], r["turn2"] or {}
    txt1 = "\n".join(t1["texts"]) + written(os.path.join(RES, f"{key}_t1.jsonl"))
    txt2 = "\n".join(t2.get("texts", [])) + written(os.path.join(RES, f"{key}_t2.jsonl"))
    allt = txt1 + "\n" + txt2
    reads = " ".join((t1["reads"] or []) + (t2.get("reads") or []))
    s = r["situation"]
    if s == "S1":
        return {
            "코드를 읽음": 1 if "todo.py" in reads else 0,
            "기존 delete 함수 유지": has(r"delete\(?\)?[^\n]{0,60}(그대로|건드리지|수정하지|유지|두)", allt),
            "테스트 포함": has(r"pytest|test_todo|테스트", allt),
            "입력 끊김(EOF) 처리": has(r"EOF", allt),
            "새 문서 파일을 만들지 않음": 0 if r["new_files"] else 1,
        }
    if s == "S2":
        return {
            "단계·주차로 나눔": has(r"주차|\d주|마일스톤|단계", allt),
            "범위(넣을 것·뺄 것)": has(r"MVP|제외|범위 밖|하지 않", allt),
            "위험 요소": has(r"위험|리스크", allt),
            "데이터 설계": has(r"데이터 모델|테이블|스키마|ERD", allt),
            "테스트 방법": has(r"테스트", allt),
            "답변 반영(Spring·MySQL·React)": 1 if all(w in txt2 for w in ("Spring", "MySQL", "React")) else 0,
        }
    if s == "S3":
        return {
            "처음에 묻거나 선택지를 줌": has(r"\?|A\)|후보|선택지", txt1),
            "답변 반영(선수과목·졸업요건)": 1 if ("선수" in txt2 and "졸업" in txt2) else 0,
            "사용자 확인 단계": has(r"인터뷰|사용성|설문|검증", allt),
            "데이터 출처·정확성": has(r"교육과정|조교|학과 사무실|정확", allt),
        }
    return {
        "기존 저장 코드를 읽음": 1 if "storage.py" in reads else 0,
        "옛 데이터 호환": has(r"get\(['\"]tags|기존 데이터|호환|마이그레이션", allt),
        "테스트 포함": has(r"pytest|테스트", allt),
        "걸러 본 목록의 번호 함정": has(r"(원래|전체)[^\n]{0,20}번호|번호[^\n]{0,20}(원래|전체)", allt),
        "코드 읽기 전에 질문하지 않음": 0 if (not t1["reads"] and r["asked"]) else 1,
    }


def main():
    rows = []
    for f in sorted(glob.glob(os.path.join(RES, "S?_*_r?.json"))):
        key = os.path.basename(f)[:-5]
        r = json.load(open(f, encoding="utf-8"))
        c = checks(r, key)
        tk = r["tokens"]
        rows.append(dict(key=key, situation=r["situation"], condition=r["condition"], rep=r["rep"],
                         score=sum(c.values()), max=len(c), detail=json.dumps(c, ensure_ascii=False),
                         tokens_in=tk["input"] + tk["cache_create"] + tk["cache_read"], tokens_out=tk["output"],
                         sec=r["sec"], skills=";".join((r["turn1"]["skills"] or []) + ((r["turn2"] or {}).get("skills") or []))))
    with open(os.path.join(RES, "_score.csv"), "w", encoding="utf-8-sig", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    by = {}
    for x in rows:
        by.setdefault((x["situation"], x["condition"]), []).append(x)
    for (s, c), xs in sorted(by.items()):
        sc = [x["score"] for x in xs]
        tot = [x["tokens_in"] + x["tokens_out"] for x in xs]
        print(f"{s} {c:<11} 점수 {sc}/{xs[0]['max']}  토큰(입력+출력) {min(tot):>7}~{max(tot):>7}  출력 평균 {int(statistics.mean(x['tokens_out'] for x in xs)):>5}  시간 평균 {statistics.mean(x['sec'] for x in xs):5.1f}초")


if __name__ == "__main__":
    main()
