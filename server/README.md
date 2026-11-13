# server/ — 서버 (Spring)

**담당: 노형원**

- 하는 일: 도구·판정 데이터를 DB에 저장하고, 화면이 부르면 판정·추천 결과를 돌려준다.
- 지킬 것: 비밀번호·API 키는 환경변수로만, 요청당 도구 수 제한(40개), "안전하다" 같은 단정 문구 쓰지 않기

## 지금 상태 (2026-11-13)
- `app/`: **Spring Boot 4 + JPA** 서버. 화면(`web/app`)이 쓰던 계산 규칙을 서버로 옮겼고, **화면 로컬 모드와 답이 똑같은지** 시험으로 확인했다.
  - 서버 시험 10개 통과(`./gradlew test`)
  - 화면↔서버 비교 시험 4개 통과(도구 36개 상세, 36개 전부 담은 630쌍 판정, 답 3가지 추천 등, `web/app/src/api.server.test.js`)
  - 브라우저로 도구 화면 → 도구함 → 질문 → 결과까지 서버 데이터로 동작 확인
- DB: 기본은 **내장 H2**(설치·비밀번호 없이 바로 실행). **MySQL**은 아래 3번으로 켠다.
  - MySQL 8.0으로도 확인함(2026-11-13, 따로 띄운 임시 MySQL): `mysql-setup.sql`로 DB·계정 만들기 → 처음 켤 때 데이터 넣기 → 다시 켜도 데이터 유지(두 번 넣지 않음) → 한글 그대로 저장 → 화면↔서버 비교 시험 4개 통과
- 아직 안 한 것: 저장 안 된 쌍을 AI로 판정(기획안 9장 결정 필요), 상황별 추천 규칙(김용현 규칙 v1 이후)

## 실행 방법
1. 서버(내장 DB): `cd server/app` → `./gradlew bootRun` (Windows는 `gradlew.bat bootRun`). http://localhost:8080/api/tools 가 열리면 성공
2. 화면을 서버에 연결: `web/app/.env.example`을 `.env.local`로 복사 → `npm run dev`
3. MySQL로 켜기
   - `app/mysql-setup.sql`의 비밀번호 칸을 바꿔 root로 한 번 실행(DB `inventory`와 같은 이름의 계정을 만듦)
   - `DB_PASSWORD=그비밀번호` 환경변수를 넣고 `./gradlew bootRun --args="--spring.profiles.active=mysql"`
   - 처음 켤 때 표를 만들고 데이터(분야 6·도구 36·판정 90쌍·시험 2개)를 한 번 넣는다. 다음부터는 있는 데이터를 그대로 쓴다.

## 부품과 하는 일
| 부품 | 하는 일 |
|---|---|
| `domain/` 표 4개 | 분야(Category), 도구(Tool), 판정(ToolPair), 직접 시험한 도구(TestedTool) |
| `seed/SeedLoader` | DB가 비어 있으면 JSON 파일을 읽어 한 번 넣음 |
| `service/ToolService` | 분야·도구 목록(분야·검색어 거르기)·도구 상세 |
| `service/JudgeService` | 담은 도구를 둘씩 짝지어 저장된 판정 찾기 → 겹치면 뺄 후보, 시험한 도구는 조건 보고 더하기 후보 |
| `web/ApiController` | 화면이 부르는 주소 |

## 주소(API)
| 주소 | 하는 일 |
|---|---|
| `GET /api/categories` | 분야 6개 |
| `GET /api/tools?category=&q=` | 도구 목록(분야, 이름·영어 설명·한국어 소개 검색) |
| `GET /api/tools/{id}` | 도구 카드 + 이 도구와 관련된 판정 |
| `GET /api/judgments?a=&b=` | 두 도구의 판정. 없으면 404("확인된 정보 없음") |
| `POST /api/judge` (`/api/box/judge`도 같음) | `{"ids": [...]}` → 모든 짝의 판정. 판정이 없으면 `state: no_info` |
| `POST /api/recommend` | `{"ids": [...], "answers": {"work","shell","logs"}}` → `pairs`·`remove`·`add`·`unknownCount` |

응답의 이름(`desc_en`, `summary_ko`, `review_state`, `otherId` 등)은 화면 로컬 모드와 같다. 자세한 모양은 `web/app/src/api.js`.

## 데이터
- `sample-data/`: `entries.json`(36개), `compat.json`(90쌍), `categories.json`(분야 6개). 기획안 6-1장 형식
- 화면 데이터 `web/app/src/data/`의 `tested.json`(시험 결과), `desc_en.json`(영어 설명), `cards_ko.json`(한국어 카드 문구)도 같이 읽는다(빌드할 때 복사, 파일을 두 벌 두지 않음)
- `api-draft.md`: 10월 초안(설계 배경)
