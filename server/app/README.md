# inventory-server

Claude Code 도구 호환성 검사 서비스 - 서버 모듈

## 버전 (임시로 정함)

| 항목 | 값 | 비고 |
|---|---|---|
| Java | 21 | 팀이 아직 버전을 결정하지 않아서 임시로 정함 |
| Spring Boot | 3.3.5 | 임시 |
| Gradle | 8.8 (Wrapper) | 임시 |

## 실행

```bash
cd server/app
./gradlew bootRun
```

기본 포트: 8080  
기본 데이터 폴더: `../sample-data` (설정값 `inventory.data-dir`)

## 테스트

```bash
./gradlew test
```

## 설정

`src/main/resources/application.properties`

```properties
inventory.data-dir=../sample-data   # JSON 데이터 폴더 (상대경로: server/app 기준)
inventory.max-tools=50              # 요청당 도구 수 상한 [결정 필요]
```

## API 요약

| 주소 | 설명 |
|---|---|
| `GET /api/categories` | 분야 6개 목록 |
| `GET /api/tools?category=&q=&sort=` | 도구 목록 |
| `GET /api/tools/{id}` | 도구 카드 + 같은 분야 판정 |
| `GET /api/judgments?a=&b=` | 두 도구 판정 (없으면 404) |
| `POST /api/box/judge` | 도구함 전체 판정 |
| `POST /api/box/recommend` | 추천(빼기·더하기) |

CORS: `http://localhost:5173`만 허용
