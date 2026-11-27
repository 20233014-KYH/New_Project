# 36개 도구 스캔 결과 (2026-11-09)

대상: 36개 전체. 앞의 12개는 2026-10-31과 같은 커밋, 새 24개는 2026-11-09에 받은 커밋입니다(`commits.json`).
모든 결과는 **사람 검수 전**입니다. "안전/위험"을 뜻하지 않습니다.

| 파일 | 내용 |
|---|---|
| `access_scope.json` / `.md` | 도구 × 접근 범위 6칸 표 |
| `signals.jsonl` | 스캐너 신호 전체 (판정 반영 630개 + 참고 1270개) |
| `mcp_tools.json` | MCP 도구 추출 결과. **표에는 앞의 12개만 씀**(아래 참고) |
| `scan_labeling.xlsx` | 사람 라벨링 시트. "AI 예비 판단"은 앞의 12개 신호에만 있음 |
| `commits.json` | 저장소별 확인한 커밋과 날짜 |

## 한눈에

- 216칸 중 찾음 86, 검사했지만 찾지 못함 61, 검사 전 36, 해당 없음 33
- 사실 줄의 근거: `pattern` 121 · `doc` 28 · `ai` 14 · `calc` 11 · `tested` 4 (모두 178줄) (`pattern`은 사람이 확인하기 전에는 화면에 쓰지 않음, 기획안 6-6)

## 2026-10-31(v3)에서 바뀐 것

- 저장소 개발자용 파일(`.github/`, `.devcontainer/`, `Dockerfile`, `Makefile`, 테스트 설정)의 원격 실행 형태는 참고로만 둠. 사용자 설치 경로가 아니기 때문
- 저장소 자체의 `.claude/settings.json` 훅과 다른 제품용 변형(claude-mem의 `cowork/`)은 참고로만 둠. Claude Code 플러그인 설치로 들어가지 않기 때문
- MCP 도구 추출기는 새 24개 형식(Go `api.Tool`, `server.tool(...)` 등)을 놓치거나 다른 패키지 도구까지 잡아서, 새 저장소의 DB·외부 서비스·브라우저 칸은 "검사 전"으로 두고 README·코드로 확인한 사실만 넣음. MCP 도구 개수는 팀 실측을 봄
- README·코드로 확인한 사실 26줄 추가(밖으로 보내기, 읽기 전용 기본값 등). `build_access.py`의 `MANUAL`에 파일:줄 근거가 있음

- 2026-11-15: 셸 명령이 없는 훅(`type: prompt`)도 셈. trailofbits 훅이 6개 → 8개(5가지 시점)로 바뀜 (PR #14 대조 중 발견)

## 사람 확인 (2026-11-28)

- 형원 님이 시험한 8개(playwright-mcp, chrome-devtools-mcp, trailofbits/skills, claude-code-security-review, superpowers, gstack, gsd-core, planning-with-files)의 사실 **57줄을 허준서가 원문과 대조해 모두 "맞음"** 으로 확인했어요(이슈 #22).
- 근거 종류는 그대로 두고 `reviewed: true`, `reviewed_by`, `reviewed_at`만 더했어요. 마크다운에는 "사람 확인함(허준서, 2026-11-28)"으로 보여요.
- 검수 기록: [`../../reviews.csv`](../../reviews.csv). 전체 178줄 중 57줄 확인, 나머지 121줄은 사람 확인 전이에요.

## 남은 확인

- 새 24개 신호의 사람 라벨(특히 R1 원격 실행 형태 중 다른 도구 설치 안내인 것)
- 새 MCP 서버 11개의 도구 추출(추출기 확장 필요)
- "밖으로 보내기" 칸이 "검사 전"인 도구들
