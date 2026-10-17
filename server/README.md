# server/ — 서버 (Spring)

**담당: ③ 서버** (정해지면 이름 적기)

- 하는 일: 저장된 판정 조회, 저장 안 된 조합만 AI로 판정, 결과 저장
- 지킬 것: API 키는 환경변수로만, 요청 수·글자 수 제한, 하루 사용 상한
- 화면이 부를 주소(초안): `GET /api/tools`, `GET /api/tools/{id}`, `GET /api/judgments?a=&b=`, `POST /api/box/judge`
