# server/ — 서버 (Spring)

**담당: 노형원**

- 하는 일: 저장된 판정 조회, 저장 안 된 조합만 AI로 판정, 결과 저장
- 지킬 것: API 키는 환경변수로만, 요청 수·글자 수 제한, 하루 사용 상한
- 화면이 부를 주소(초안): `GET /api/tools`, `GET /api/tools/{id}`, `GET /api/judgments?a=&b=`, `POST /api/box/judge`

## API·데이터 초안 (2026-10-26)
- `api-draft.md`: API 6개, 판정 상태(`state`), 추천 규칙, Spring 클래스 초안이에요.
- `sample-data/`: 실측과 김용현 1차 검수로 만든 `entries.json`(36개), `compat.json`(90쌍)이에요. 기획안 6-1장 형식이에요.
