# server 진행 기록

> 작업 지시: `server/cloud-task.md`. 커밋할 때마다 이 파일도 같이 고쳐서 push한다.
> 세션이 끊기면 다음 사람(클라우드든 로컬이든)은 "다음 한 걸음"부터 이어서 한다.

## 다음 한 걸음
- MySQL로 한 번 켜 보기(`server/README.md` 3번, 형원이 비밀번호 넣고 실행)
- 김용현 추천 규칙 v1이 나오면 `JudgeService.recommend`의 임시 규칙(토큰 큰 쪽 빼기)을 상황 기준으로 바꾸기
- 저장 안 된 쌍 AI 판정(기획안 9장 결정 뒤)

## 끝난 것
- (2026-11-13) `server/app/` Spring Boot 4 + JPA 서버. DB에 분야·도구·판정·시험 결과 저장, API 6개, 화면 로컬 모드와 답 일치 확인(서버 시험 10개 + 화면↔서버 비교 4개), 화면을 서버에 연결(`web/app/.env.example`). 한국어 카드 문구 36개(`web/app/src/data/cards_ko.json`) (노형원)
- (2026-10-26) API 초안 `server/api-draft.md`, 샘플 데이터 `server/sample-data/` (노형원, PR #8)

## 진행 중

## 막힌 것

## 물어볼 것 (형원에게)
