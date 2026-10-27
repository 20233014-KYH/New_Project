# web 진행 기록

> 작업 지시: `web/cloud-task.md`. 커밋할 때마다 이 파일도 같이 고쳐서 push한다.
> 세션이 끊기면 다음 사람(클라우드든 로컬이든)은 "다음 한 걸음"부터 이어서 한다.

## 다음 한 걸음
- 홈 화면(`HomePage.jsx`) 구현: 와이어프레임 `#home` 화면 그대로
  - 큰 검색창, 자동완성 목록, "처음이에요"/"둘러보기" 입구 카드 2개
  - 오른쪽 "사용 방법" 3단계 안내, 아래 하이라이트 사실 카드

## 끝난 것
- (2026-10-28) 확정 디자인 와이어프레임 `web/wireframe/v2/` 올림 (노형원)
- (2026-10-27) `web/app/` Vite + React + Tailwind 최소 구성
  - `npm run build` 오류 없이 통과
  - `npm test` 4개 모두 통과 (판정·추천 로컬 모드 계산 시험)
  - 라우팅 10개 화면 스켈레톤: home, start, browse/:categoryId, find, tool/:id, box, ask/1, ask/2, result, help
  - `src/api.js`: 로컬 모드 판정·추천 계산 (logic.js 포팅), API 함수 6개
  - `src/data/`: entries.json, compat.json, tested.json 복사

## 진행 중

## 막힌 것

## 물어볼 것 (형원에게)
