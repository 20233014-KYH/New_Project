# 측정 중에 도구가 실험 폴더 밖에 남긴 것 (2026-10-18)

도구 하나만 켜고 "ok" 질문을 2번 보낸 것 말고는 아무 일도 안 시켰어요.
그런데도 아래 파일들이 사용자 폴더에 생겼어요. 측정이 끝난 뒤 모두 지웠어요.

| 도구 | 생긴 것 | 내용 |
|---|---|---|
| caveman | `~/.claude/.caveman-active`, `.caveman-mode-log.jsonl`, `.caveman-nudge-shown`, `.caveman-sessions/`, `~/.claude/hooks/caveman-statusline.ps1` | 세션별 모드 기록, 상태줄 스크립트 사본 |
| gsd-core | `~/.claude/gsd-core/` (바로가기 5개: bin, contexts, references, templates, workflows) | 세션이 시작될 때 플러그인 폴더를 가리키는 바로가기를 사용자 설정 폴더에 만들어요 |
| codegraph | `~/.codegraph/telemetry-queue.jsonl`, `update-check.json` | **사용 기록(텔레메트리) 대기열**(`"k":"cli_command","n":"serve"`)과 새 버전 확인 기록 |
| serena | `~/.serena/` (설정 파일, 로그, 메모리 폴더) | 처음 실행할 때 전역 설정을 만들어요 |
| claude-context | `~/.context/` (빈 폴더) | |
| context7 (플러그인) | `~/.claude/mcp-needs-auth-cache.json` | 원격 MCP가 로그인을 요구해서 Claude Code가 남긴 기록. context7는 로그인 없이는 도구가 안 붙었어요 |
| Figma-Context-MCP | (파일 없음) | 실행하면 "Usage telemetry enabled. Disable: FRAMELINK_TELEMETRY=off or DO_NOT_TRACK=1"라고 출력해요. **기본값이 사용 기록 보내기 켜짐** |

참고
- 측정할 때는 `DO_NOT_TRACK=1`, `FRAMELINK_TELEMETRY=off`를 넣었어요. 하지만 codegraph는 그래도 대기열 파일을 만들었어요. 실제로 밖으로 보냈는지는 확인 안 했어요.
- 이 표는 "ok" 질문 한 번에 생긴 것만이에요. 실제로 쓰면 더 많은 파일을 만들 수 있어요.
