#!/usr/bin/env python3
"""시험 3 v3 자동 채점(함정 항목). AI 채점 없이 미리 정한 항목이 답에 있는지 정해진 규칙으로 확인한다.

- 본 글: 첫·두 번째 대답의 글 + 파일에 쓴 내용
- 결과: results_v3/_score.csv, 화면에 상황·조건별 점수와 항목별로 놓친 횟수
사용법: python score_v3.py
"""
import csv
import glob
import json
import os
import statistics
import sys

from score_v2 import has, written

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results_v3")


def checks(r, key):
    t1, t2 = r["turn1"], r["turn2"] or {}
    txt1 = "\n".join(t1["texts"]) + written(os.path.join(RES, f"{key}_t1.jsonl"))
    txt2 = "\n".join(t2.get("texts", [])) + written(os.path.join(RES, f"{key}_t2.jsonl"))
    allt = txt1 + "\n" + txt2
    reads = " ".join((t1["reads"] or []) + (t2.get("reads") or []))
    s = r["situation"]
    if s == "S2":
        return {
            "단계·주차": has(r"주차|\d주|마일스톤", allt),
            "범위(뺄 것)": has(r"제외|범위 밖|하지 않|2차|나중", allt),
            "데이터 설계": has(r"데이터 모델|테이블|스키마|ERD", allt),
            "테스트": has(r"테스트", allt),
            "답변 반영": 1 if all(w in txt2 for w in ("Spring", "MySQL", "React")) else 0,
            "남의 데이터 접근 막기": has(r"IDOR|본인 (데이터|것)만|권한 검사|서버에서 (권한|역할)", allt),
            "개인정보 동의·최소 수집": has(r"개인정보.{0,20}(동의|최소)|수집.{0,10}동의|최소한(만)? 수집", allt),
            "실제 사용자 시범 사용": has(r"시범|파일럿|실사용|사용성 테스트|임원.{0,15}(테스트|사용)", allt),
            "백업": has(r"백업", allt),
            "인수인계·운영 문서": has(r"인수인계|운영 (문서|매뉴얼)|관리자 매뉴얼|다음 (임원|담당)", allt),
        }
    if s == "S3":
        return {
            "처음에 묻거나 선택지": has(r"\?|A\)|후보|선택지", txt1),
            "답변 반영": 1 if ("선수" in txt2 and "졸업" in txt2) else 0,
            "데이터 출처": has(r"교육과정|조교|학과 사무실", allt),
            "틀린 정보 대비(참고용·기준일)": has(r"참고용|면책|공식 기준|기준 연도|기준일", allt),
            "입학년도별 차이": has(r"입학 ?년도|학번별|연도별", allt),
            "사용자 확인": has(r"인터뷰|사용성|설문", allt),
            "범위 줄이기": has(r"제외|하지 않|2순위|나중|범위 밖", allt),
        }
    if s == "S5":
        return {
            "일정이 무리라고 지적": has(r"무리|불가능|현실적으로|빠듯|일주일.{0,30}(부족|어렵|안 됩)|1주.{0,30}(부족|어렵|안 됩)", allt),
            "우선순위·뺄 것": has(r"우선순위|빼|제외|나중|2차|다음 단계|뒤로", allt),
            "카드 결제 대안": has(r"PG|사업자|심사|계좌|송금|수기|현금", allt),
            "개인정보 동의·최소 수집": has(r"개인정보.{0,20}(동의|보호|최소)|수집.{0,10}동의|최소한", allt),
            "이미 있는 도구 활용": has(r"구글 ?폼|스프레드시트|노션|Google ?(Forms|Sheets)|오픈채팅|기존 서비스|노코드", allt),
            "행사에 필요한 것 먼저": has(r"행사.{0,40}(출석|당일|먼저)|출석.{0,30}(먼저|우선|핵심)", allt),
            "답변 반영(무료·파이썬)": has(r"무료|0원|파이썬|Python", txt2),
        }
    if s == "S7":
        return {
            "문제 정의": has(r"문제|불편|페인|pain", allt),
            "대상 사용자": has(r"사용자|페르소나|임원.{0,15}회원|회원.{0,15}임원", allt),
            "목표·성공 지표": has(r"지표|KPI|성공 기준|측정", allt),
            "하지 않을 것(비목표)": has(r"비목표|범위 밖|하지 않|제외|Non-?goal", allt),
            "요구사항 우선순위": has(r"우선순위|필수|Must|P0|MVP", allt),
            "가정·위험": has(r"가정|위험|리스크|Assumption", allt),
            "현재 방식 반영(엑셀·카톡)": 1 if ("엑셀" in txt2 and "카톡" in txt2) else 0,
            "사용자 확인 방법": has(r"인터뷰|설문|검증|시범|파일럿", allt),
        }
    return {
        "명령줄 코드를 읽음": 1 if "cli.py" in reads else 0,
        "웹 코드를 읽음": 1 if "web.py" in reads else 0,
        "두 곳 모두 고침": 1 if ("cli.py" in allt and "web.py" in allt) else 0,
        "같은 표시 코드 중복 정리": has(r"중복|공통|한 곳|공유 함수|헬퍼|같은 (정보|로직)", allt),
        "저장 버전·migrate 활용": has(r"version.{0,10}3|버전 ?3|migrate", allt),
        "날짜 형식": has(r"YYYY-MM-DD|ISO|isoformat|날짜 형식|fromisoformat", allt),
        "오늘 경계": has(r"오늘.{0,30}(포함|경계|당일|지난|이전)|당일|경계", allt),
        "마감 없는 항목": has(r"마감.{0,10}(없는|이 없|미지정)|due.{0,15}(None|null)|선택 사항|optional", allt),
        "테스트": has(r"테스트|pytest", allt),
    }


def main():
    rows, miss = [], {}
    for f in sorted(glob.glob(os.path.join(RES, "S?_*_r?.json"))):
        key = os.path.basename(f)[:-5]
        r = json.load(open(f, encoding="utf-8"))
        c = checks(r, key)
        tk = r["tokens"]
        for k, v in c.items():
            if not v:
                miss.setdefault((r["situation"], r["condition"]), []).append(k)
        rows.append(dict(key=key, situation=r["situation"], condition=r["condition"], rep=r["rep"],
                         score=sum(c.values()), max=len(c), detail=json.dumps(c, ensure_ascii=False),
                         tokens_in=tk["input"] + tk["cache_create"] + tk["cache_read"], tokens_out=tk["output"],
                         sec=r["sec"], skill_count=r["turn1"]["skill_count"]))
    with open(os.path.join(RES, "_score.csv"), "w", encoding="utf-8-sig", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    by = {}
    for x in rows:
        by.setdefault((x["situation"], x["condition"]), []).append(x)
    for (s, c), xs in sorted(by.items()):
        tot = [x["tokens_in"] + x["tokens_out"] for x in xs]
        m = {}
        for k in miss.get((s, c), []):
            m[k] = m.get(k, 0) + 1
        print(f"{s} {c:<11} 점수 {[x['score'] for x in xs]}/{xs[0]['max']}  토큰 {min(tot):>7}~{max(tot):>7}  "
              f"시간 {statistics.mean(x['sec'] for x in xs):5.1f}초  스킬수 {xs[0]['skill_count']}  놓침 {m}")


if __name__ == "__main__":
    main()
