# Claude Code 기본 기능 분야별 목록 (확인 대상, 2026-10-18)

우리가 모은 36개는 **모두 외부 오픈소스**예요. Claude Code에 원래 들어 있는 기능은 빠져 있어요.
그런데 기본 기능과 오픈소스가 **같은 일을 하는 경우**가 있어요. 이것도 겹침이 될 수 있어서 따로 확인해야 해요.

- 목록 출처: 플러그인을 하나도 안 켠 Claude Code 2.1.191의 시작 기록(측정 기록 `_none`)
- **이름만 보고 분야를 나눈 것**이에요. 기능 설명은 **확인 안 됨**이에요. 실제로 무엇을 하는지는 직접 써 보고 확인해야 해요.
- 기본 기능 목록은 Claude Code 서버 설정에 따라 바뀌어요. 예: 측정 도중 `schedule` 스킬과 도구 4개가 사라졌어요.

| 분야 | 기본 기능 (이름) | 종류 | 겹칠 수 있는 오픈소스 (후보) |
|---|---|---|---|
| 1 기획·작업 방식 | Plan, general-purpose | 에이전트 | superpowers, ECC, gstack, gsd-core |
| | TaskCreate / TaskList / TaskUpdate 등 | 도구 | planning-with-files |
| | batch, loop | 스킬 | gsd-core |
| | /goal, /init | 명령 | |
| | CronCreate, ScheduleWakeup | 도구 | |
| | EnterWorktree / ExitWorktree | 도구 | superpowers(using-git-worktrees) |
| 2 토큰·컨텍스트 | /compact, /context, /clear, /usage | 명령 | caveman, headroom, ccusage |
| | ToolSearch (MCP 도구를 필요할 때 찾아 읽기) | 도구 | |
| | statusline-setup | 에이전트 | claude-hud (상태줄 자리 하나) |
| 3 코드 이해·검색 | Explore | 에이전트 | serena, codegraph, graphify, Understand-Anything |
| | Glob, Grep, Read | 도구 | claude-context, codegraph |
| | WebFetch, WebSearch | 도구 | context7 |
| | claude-api | 스킬 | context7 (문서 찾기) |
| 4 디자인·프론트엔드 | design-sync, DesignSync | 스킬·도구 | Figma MCP 2개 |
| | run | 스킬 | playwright-mcp, chrome-devtools-mcp |
| 5 백엔드·인프라 | Bash | 도구 | rtk (Bash 출력 줄이기) |
| | update-config, fewer-permission-prompts | 스킬 | |
| 6 QA·테스트 | code-review, /review | 스킬·명령 | open-code-review, trailofbits의 리뷰 스킬 |
| | /security-review | 명령 | claude-code-security-review, trailofbits |
| | verify, debug | 스킬 | superpowers(verification, systematic-debugging), tdd-guard |
| | simplify | 스킬 | ECC 일부 |

**전체 목록 (측정 기록 그대로)**
- 스킬 12개: design-sync, update-config, verify, debug, code-review, simplify, batch, fewer-permission-prompts, loop, claude-api, run, run-skill-generator
- 명령 27개: 위 스킬 12개 + clear, compact, config, context, heapdump, init, reload-skills, review, security-review, usage-credits, extra-usage, usage, insights, goal, team-onboarding
- 도구 26개: Task, Bash, CronCreate, CronDelete, CronList, DesignSync, Edit, EnterWorktree, ExitWorktree, Glob, Grep, NotebookEdit, Read, ScheduleWakeup, SendMessage, Skill, TaskCreate, TaskGet, TaskList, TaskOutput, TaskStop, TaskUpdate, ToolSearch, WebFetch, WebSearch, Write
- 에이전트 6개: claude, claude-code-guide, Explore, general-purpose, Plan, statusline-setup
