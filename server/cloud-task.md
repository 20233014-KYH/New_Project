# 작업 지시: 서버 만들기 (Spring)

> 노형원(ROH) 담당 `server/` 작업을 Claude Code(클라우드 또는 로컬)가 이어서 하기 위한 지시서예요.
> **시작할 때마다 이 파일과 `server/PROGRESS.md`를 먼저 읽고, `PROGRESS.md`의 "다음 한 걸음"부터 이어서 하세요.**

## 목표
`server/api-draft.md`의 API 6개를 **Spring Boot**로 만든다. 데이터는 `server/sample-data/entries.json`(36개), `compat.json`(90쌍)을 읽는다.

## 꼭 지킬 것
1. **기획을 바꾸지 않는다.** 규칙은 `server/api-draft.md`와 `docs/proposal-ROH.md`(6-1, 6-3, 6-5장) 그대로. 애매하면 바꾸지 말고 `PROGRESS.md`의 "물어볼 것"에 적는다.
2. **`server/` 폴더만 고친다.** `docs/`, `judgment/`, `data/`, `web/`는 읽기만 한다.
3. **브랜치 `ROH-server`에서만 작업**하고 push한다. `main`·`ROH`에 push하지 않는다. PR은 만들지 않는다.
4. **작은 단계마다 커밋하고 바로 push**한다(클래스 묶음 하나, API 하나 단위). 커밋할 때 `server/PROGRESS.md`도 같이 고친다.
5. 키·토큰을 파일에 쓰지 않는다. AI 호출 코드는 만들지 않는다(아래 범위 밖).
6. 응답 문구에 "안전합니다" 같은 단정을 넣지 않는다. 판정 없는 쌍은 `state: "no_info"`.

## 만들 것
- 위치: `server/app/` (Gradle, Java 17, Spring Boot 3.x). 팀이 아직 버전을 정하지 않아서 이 값으로 시작하고, `server/app/README.md`에 "임시로 정함"이라고 적는다.
  - 시작 전에 `java -version`을 확인한다. Java 17 이상이 없고 설치도 안 되면, 멈추고 `PROGRESS.md`의 "막힌 것"에 적는다.
- `sample-data/*.json`은 복사하지 말고 실행할 때 경로로 읽는다(설정값 `inventory.data-dir`, 기본 `../sample-data`).
- 직접 시험 결과(caveman·rtk 효과와 주의 문구, 조건 `caution_work`·`caution_shell`)는 `web/wireframe/v2/data.js`의 `tested` 배열에 있다. 이걸 `server/sample-data/tested.json`으로 옮기고 `_note`에 출처(judgment/experiments/2026-10-18-statusline-caveman-rtk)를 적는다.
- 클래스는 api-draft 3장 표를 따른다: `Tool`, `Scope`, `AutoMeta`, `Judgment`, `Evidence`, `ToolRepository`/`JudgmentRepository`(인터페이스, JSON 구현부터), `JudgmentService.judgeBox()`, `RecommendService`, `PairKey`.
- API 6개: `GET /api/categories`, `GET /api/tools?category=&q=&sort=`, `GET /api/tools/{id}`, `GET /api/judgments?a=&b=`, `POST /api/box/judge`, `POST /api/box/recommend`.
  - 분야 6개 이름·설명·"이럴 때"는 `web/wireframe/v2/data.js`의 `categories`와 같아야 한다.
  - `outdated`, 정렬·중복 제거, 도구 0~1개면 빈 목록, 3개 이상이면 `range_note`, 목록에 없는 도구는 `unknown_tools` (api-draft 2장).
  - 요청당 도구 수 상한은 아직 결정 전이다. 설정값 `inventory.max-tools`(임시 기본 50)로 두고 "결정 필요"라고 주석을 단다.
- 웹이 다른 포트에서 부를 수 있게 CORS는 `http://localhost:5173`만 연다.

## 다 됐는지 확인하는 법
- `cd server/app && ./gradlew test`가 통과한다. 최소 이것들:
  - judge [superpowers, ecc, caveman] → superpowers×ecc는 `saved`/`overlap`, caveman 쌍은 `no_info`
  - (b, a) 순서로 물어도 (a, b)와 같은 판정
  - recommend [superpowers, ecc], shell=powershell → remove에 ecc(`save_tokens_max` 9169), add의 rtk에 PowerShell 주의
  - 없는 도구 id → `unknown_tools`, 판정 없는 쌍 조회 → 404
- `./gradlew bootRun` 후 `curl localhost:8080/api/categories`가 6개를 돌려준다.

## 범위 밖 (하지 말 것)
- 미저장 쌍 AI 판정 호출(`ai_pending`/`ai_estimate`): 쓸 AI가 결정 전이다. `state` 값과 인터페이스 자리만 둔다.
- DB: JSON으로 시작한다(기획 결정).
- 교체 추천(`replace`): MVP 이후. 빈 배열로 둔다.
