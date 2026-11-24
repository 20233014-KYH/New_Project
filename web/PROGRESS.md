# web 진행 기록

> 작업 지시: `web/cloud-task.md`. 커밋할 때마다 이 파일도 같이 고쳐서 push한다.
> 세션이 끊기면 다음 사람(클라우드든 로컬이든)은 "다음 한 걸음"부터 이어서 한다.

## 다음 한 걸음
✅ cloud-task.md의 모든 항목 완료. 추가 작업 없음.
- 형원이 확인 후 ROH-front → main PR 생성 가능

## 끝난 것
- (2026-10-28) 확정 디자인 와이어프레임 `web/wireframe/v2/` 올림 (노형원)
- (2026-10-27) `web/app/` Vite + React + Tailwind 최소 구성
  - `npm run build` 오류 없이 통과
  - `npm test` 4개 모두 통과 (판정·추천 로컬 모드 계산 시험)
  - 라우팅 10개 화면 스켈레톤: home, start, browse/:categoryId, find, tool/:id, box, ask/1, ask/2, result, help
  - `src/api.js`: 로컬 모드 판정·추천 계산 (logic.js 포팅), API 함수 6개
  - `src/data/`: entries.json, compat.json, tested.json 복사
- (2026-10-27) 11개 화면 전체 구현 + 공통 컴포넌트 + CSS 전체 스타일
  - HomePage: 큰 검색창(자동완성), 경로 카드 2개, 사용 방법 3단계, 하이라이트 사실 카드
  - StartPage: 카테고리 6개 선택, 선택 시 토큰 낮은 도구 3개 표시
  - BrowsePage: 카테고리 탭, 검색+정렬, 겹침 표시
  - FindPage: ?q= 검색 결과 목록
  - ToolPage: 상세(토큰 바, 역할 범위 바, 쌍 목록, 스펙 사이드바)
  - BoxPage: 도구함(카테고리별 슬롯, 판정 결과, 빈 상태/채운 상태)
  - Ask1Page: 작업 유형 질문(3지선다), 미선택 시 오류 안내
  - Ask2Page: 셸 환경 질문(3지선다), 미선택 시 오류 안내
  - ResultPage: 빼기 추천 + 더하기 추천 + 이렇게 골랐어요
  - HelpPage: 용어 풀이 + FAQ
  - Steps, AddButton 공통 컴포넌트
  - index.css: 와이어프레임 모든 CSS 변수·클래스 포팅
- (2026-10-27) cloud-task.md 확인 항목 전체 통과 (Playwright)
  - 모바일 390px: 10개 화면 + 도구함(채움) 가로 오버플로 없음
  - 전체 흐름: 홈 검색 → 담기(빼기 전환) → 도구함(겹침 표시) → 질문1(미선택 오류) → 질문2(미선택 오류) → 결과(Steps 3단계)
  - `npm run build` 오류 없음, `npm test` 4개 통과

## 진행 중

## 막힌 것

## 물어볼 것 (형원에게)
