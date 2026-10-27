# server 진행 기록

> 작업 지시: `server/cloud-task.md`. 커밋할 때마다 이 파일도 같이 고쳐서 push한다.
> 세션이 끊기면 다음 사람(클라우드든 로컬이든)은 "다음 한 걸음"부터 이어서 한다.

## 다음 한 걸음
- `./gradlew bootRun` 후 `curl localhost:8080/api/categories` 로 6개 응답 직접 확인
- 판단 없는 쌍 조회(`GET /api/judgments?a=superpowers&b=caveman`) → 404 확인
- `ToolController.get()` 의 `judgments` 필터 개선 (같은 도구끼리 쌍이 아닌 버그 제거)

## 끝난 것
- (2026-10-26) API 초안 `server/api-draft.md`, 샘플 데이터 `server/sample-data/` (노형원, PR #8)
- (2026-10-27) Spring Boot 3.3.5 + Gradle 8.8 기반 `server/app/` 구성, API 6개 구현, 테스트 통과 (Claude, ROH-server)
  - 도메인: `Tool`, `Scope`, `AutoMeta`, `Judgment`, `Evidence`, `PairKey`, `TestedInfo`
  - 저장소: `ToolRepository`, `JudgmentRepository` 인터페이스 + JSON 구현체, `TestedRepository`
  - 서비스: `JudgmentService.judgeBox()`, `RecommendService`
  - 컨트롤러: `CategoryController`, `ToolController`, `JudgmentController`, `BoxController`
  - `server/sample-data/tested.json` 생성 (web/wireframe/v2/data.js에서 옮김)
  - `./gradlew test` 통과: judgeBox 3개, 역방향 동일 판정, recommend powershell, unknown_tools

## 진행 중

## 막힌 것
- Maven Central 속도 제한(429): 의존성 다운로드 시 간헐적으로 실패. 재시도하면 해결됨.

## 물어볼 것 (형원에게)
- `inventory.max-tools` (요청당 도구 수 상한): 임시 50으로 설정. 최종값 결정 필요.
- Java / Spring Boot 버전: 임시 Java 21 / Spring Boot 3.3.5 사용. 팀 확정 필요.
