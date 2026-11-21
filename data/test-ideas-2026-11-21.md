# 아직 시험 안 한 도구: 실제 쓰이는 상황과 정답 있는 시험 과제 (2026-11-21)

담당: 허준서 · 이슈 #22 필수 2·3번 · 형원 님 시험 6(`prototype/tool-tests-2026-11/시험6_남은분야/진행기록.md`, PR #25)을 먼저 읽고, **아직 시험하지 않은 도구만** 골랐어요.

**주의**: "실제 쓰이는 상황"은 블로그·후기·공식 문서를 읽고 정리한 거예요. 우리가 확인한 사실이 아니라 **시험할 상황을 고르는 근거**로만 써요(형원 님 `조사_실사용상황.md`와 같은 방식). 시험 과제는 초안이라 형원 님이 돌리기 전에 고쳐도 돼요.

## 0. 이미 시험한 것 (다시 안 함)

형원 님 시험 3~6에서 끝난 것: 기획 6개(superpowers, ECC, gstack, gsd-core, planning-with-files, pm-skills), QA(playwright, chrome-devtools, `/security-review`), 토큰(rtk, headroom, caveman, claude-mem, claude-hud, ccusage), 코드 검색(graphify, codegraph, serena, context7), 서버(dbhub, mcp-toolbox의 SQLite, terraform-mcp-server).

**남은 도구 14개**: 디자인 6개(impeccable, taste-skill, ui-ux-pro-max, Figma-Context-MCP, cursor-talk-to-figma-mcp, shadcn-ui-mcp-server) · 코드 검색 2개(Understand-Anything, claude-context) · 서버 3개(kubernetes-mcp-server, mcp-server-kubernetes, supabase) · QA 3개(tdd-guard, open-code-review, trailofbits 깊은 감사).
디자인 3개는 형원 님 6-7(블라인드 비교)이 예정돼 있어서, 여기서는 **블라인드 전에 자동으로 채점할 수 있는 과제**를 보탰어요.

## 1. 한눈에: 상황 → 시험 과제

| # | 분야 | 상황(쉬운 말) | 조건 | 정답·채점 | 준비물 | 바로 돌릴 수 있나 |
|---|---|---|---|---|---|---|
| D1 | ④ | 이미 만든 화면을 다듬고 싶어요 | 없음 / impeccable / taste-skill / ui-ux-pro-max | 일부러 심은 결함 10개 중 몇 개 고쳤나(자동) + 새로 생긴 접근성 오류 | Playwright, axe-core | **됨** |
| D2 | ④ | 우리 업종(병원·은행 등)에 맞는 색·글꼴을 정하고 싶어요 | 없음 / ui-ux-pro-max / impeccable | 측정 가능한 것만 자동(글자 대비 AA, 글꼴 수, 색 수, 간격 배수) + 어울림은 블라인드 | Playwright | **됨** (반은 사람) |
| D3 | ④ | 새 랜딩 페이지가 "AI가 만든 티"가 안 나게 하고 싶어요 | 없음 / taste-skill / impeccable | "흔한 AI 모양" 지표 개수(Inter 글꼴, 보라 그라데이션, 이모지 아이콘 등) + 블라인드 | Playwright | 됨, **taste-skill은 1번에 30~45분** |
| D4 | ④ | shadcn/ui 컴포넌트를 정확히 넣고 싶어요 | 없음 / shadcn-ui-mcp-server / **공식 shadcn MCP** | 빌드·타입 검사 통과, 파일 위치·import가 레지스트리 원문과 같은가 | Next.js+shadcn 예제 | **됨** |
| D5 | ④ | Figma 시안을 코드로 옮기고 싶어요 | 없음(스크린샷) / Figma-Context-MCP | 요소 위치·크기·색·글자 크기가 Figma 값과 오차 안에 드는가(자동) | **Figma 무료 계정 + 토큰** | 계정 만들면 됨 |
| D6 | ④ | Figma에서 반복 수정(글자 20개 바꾸기)을 시키고 싶어요 | cursor-talk-to-figma-mcp(+사람 손 시간) | 바꾼 뒤 Figma API로 읽어 20개가 정확히 바뀌었나 | Figma 계정 + 플러그인 + WebSocket 서버 | 계정 만들면 됨 |
| U1 | ③ | 처음 보는 큰 코드를 익히고 싶어요(온보딩) | 없음 / Understand-Anything / codegraph | 형원 님 6-3b T3(시작점 없이 흐름 묻기) 정답표 그대로 + **처음 분석 비용** | 6-3b 코드 그대로 | **됨** |
| U2 | ③ | 함수 이름을 몰라서 뜻으로만 찾아야 해요 | 없음 / claude-context(로컬) | 단어가 안 겹치는 질문 6개, 정답 파일 목록 대비 찾은 비율 | **Docker(Milvus) + Ollama** | 설치하면 됨, 무료 |
| K1 | ⑤ | 쿠버네티스에서 서비스가 안 떠요, 원인을 찾고 싶어요 | 없음(kubectl) / kubernetes-mcp-server / mcp-server-kubernetes | 일부러 심은 고장 5개 중 원인 맞힘 + "고쳐 줘" 했을 때 클러스터를 바꿨나 | **Docker + kind** | 설치하면 됨, 무료 |
| S1 | ⑤ | Supabase DB에 테이블·권한(RLS)을 추가하고 싶어요 | 없음(supabase CLI) / supabase MCP | 마이그레이션 뒤 스키마·RLS를 SQL로 확인 + 읽기 전용에서 막히나 | Docker + Supabase CLI | **확인 필요**(로컬에서 계정 없이 되는지) |
| T1 | ⑥ | Claude가 테스트보다 구현을 먼저 써요 | 없음 / CLAUDE.md 규칙 / superpowers / tdd-guard | 기능 3개마다 "테스트 파일을 먼저 썼나"(도구 호출 순서로 자동) + 테스트 통과 | 작은 예제 저장소 | **됨** |

시험 못 하거나 조건이 붙는 도구는 3장에 따로 모았어요.

## 2. 상황별 자세히

### ④ 디자인

**사람들이 쓰는 상황 (출처)**
- 아무 지시 없이 만들면 화면이 "Inter 글꼴, 흰 바탕에 보라 그라데이션, 움직임 최소"로 비슷해진다는 문제가 있고, 디자인 스킬은 이걸 피하려고 씀 — Anthropic 블로그, 2025-11-12 ([링크](https://claude.com/blog/improving-frontend-design-through-skills)). 숫자 기준은 없고 전후 화면 비교만 있음.
- impeccable: 자기 사이트를 다듬는 중에 `document`로 지금 디자인을 정리하고 `critique`로 점수를 매겨, 위 2개 지적을 고쳤더니 25/40 → 32/40. 장식 점검으로 결과가 "보통 3분의 1 가벼워짐". 불만: 명령·참고 자료가 컨텍스트를 꽤 차지해서 디자인할 때만 켬, 서양 모더니즘 쪽으로 치우침 — 개인 후기 ([mejba.me](https://www.mejba.me/blog/impeccable-claude-code-design-skill), 날짜 표시 없음)
- taste-skill, ui-ux-pro-max: 스킬 목록 사이트에만 있고 **사용 후기를 찾지 못했어요**(tessl·skills 목록 페이지뿐). 시험할 상황은 README의 주장(taste: 새 페이지, ui-ux-pro-max: 업종별 디자인 시스템)으로 정했어요.
- Figma: 공식 Figma MCP는 **유료 Dev 좌석**이 필요하고, Framelink(=Figma-Context-MCP)는 무료 계정 + 개인 토큰으로 됨. 프레임 링크로 가입 화면을 "첫 시도에 거의 픽셀 그대로" 만들었지만 모서리 둥글기가 반대쪽으로 가는 등 틀린 곳이 있었음 — LogRocket, 2025-11 ([링크](https://blog.logrocket.com/ux-design/design-to-code-with-figma-mcp/)). 공식 MCP 후기에서는 "이미 있는 코드는 못 고침", "프레임마다 따로 변환" — Builder.io, 2025-07 ([링크](https://www.builder.io/blog/claude-code-figma-mcp-server))
- shadcn: **shadcn 공식 MCP 서버가 따로 있어요**(`npx shadcn@latest mcp`, Claude Code 지원). 컴포넌트를 찾고 프로젝트에 바로 설치까지 함 ([ui.shadcn.com/docs/mcp](https://ui.shadcn.com/docs/mcp)). 우리 목록의 Jpisnice/shadcn-ui-mcp-server는 제3자 도구라 **공식과 겹치는지 시험이 필요**해요.

**D1. 이미 만든 화면 다듬기 (정답 있음)**
- 준비: 평범한 설정 화면 HTML 1장에 결함 10개를 일부러 심어 둠. 정답표 = 이 10개.
  1. 글자 대비 부족(회색 글자 #999 on #fff) 2. 이미지 alt 없음 3. 버튼 focus 스타일 없음 4. 입력칸 label 없음 5. 제목 순서 건너뜀(h1 → h4) 6. 터치 영역 44px 미만 7. 간격이 4px 배수가 아님(13px, 7px) 8. 글꼴 4종 섞임 9. 이모지를 아이콘으로 씀 10. 보라 그라데이션 배경
- 시킬 말(모든 조건 같음): "이 화면을 더 좋게 다듬어 줘. 내용과 기능은 그대로 둬."
- 채점(자동, Playwright): 1~6은 axe-core 규칙(`color-contrast`, `image-alt`, `label`, `heading-order`, `target-size`)과 `:focus-visible` 스타일 검사, 7~10은 계산된 CSS에서 셈. **내용이 그대로인지**(원래 글자·버튼 수)도 확인 → 지웠으면 그 항목 0점.
- 비교 대상에 디자인 파일럿(`docs/design-pilot-result.md`, 간격 4px 배수 90% 등)과 같은 지표를 넣어 이어 볼 수 있어요.

**D2. 업종에 맞는 디자인 시스템 (반은 정답 있음)**
- 시킬 말: "병원 예약 앱의 첫 화면을 만들어 줘" / "증권 앱 첫 화면" 2가지.
- 자동 채점: 모든 글자 대비 WCAG AA 이상, 글꼴 2종 이하, 주요 색 5개 이하, 간격 4px 배수 비율. **어울리는지**는 형원 님 블라인드(6-7)로.
- ui-ux-pro-max가 "업종 규칙 192개"로 고른 색·글꼴이 실제 화면에 반영됐는지는 스킬이 남긴 추천 결과와 CSS 값을 비교해 확인.

**D3. 새 랜딩 페이지의 "AI 티" (지표 + 블라인드)**
- 시킬 말: "작은 커피 로스터리의 랜딩 페이지를 만들어 줘."
- 자동 지표(낮을수록 덜 흔함): Inter·system 글꼴만 씀 / 보라·파랑 그라데이션 / 이모지 아이콘 / "가운데 큰 제목 + 카드 3개" 배치 / 그림자·둥근 모서리가 모든 요소에. 지표는 Anthropic 블로그가 든 예를 따름.
- **taste-skill 비용 주의**: 제작자가 한 번에 30~45분, 토큰 수십만 개라고 밝힘 → 3번 대신 1~2번만, 비용을 따로 기록.
- impeccable의 자체 검사 규칙(62개)은 impeccable 쪽에 유리할 수 있어서 **채점에 쓰지 않음**.

**D4. shadcn 컴포넌트 넣기 (정답 있음)**
- 준비: Next.js + shadcn/ui가 설정된 빈 예제. 정답 = shadcn 레지스트리 원문(v4)의 파일 위치·import 경로.
- 시킬 말: "이 프로젝트에 shadcn의 Data Table과 Combobox를 써서 사용자 목록 화면을 만들어 줘."
- 채점(자동): `npm run build`·`tsc` 통과 / `components/ui/`에 레지스트리와 같은 파일이 생겼나 / 없는 props·옛 API를 썼나(빌드 오류로 잡힘) / 토큰·시간.
- 조건에 **공식 shadcn MCP**를 꼭 넣기. 공식이 같은 일을 하면 Jpisnice 도구는 "공식으로 충분"이 될 수 있어요.

**D5·D6. Figma (계정 필요)**
- Figma 무료 계정 + 개인 접근 토큰이면 Figma-Context-MCP는 돌릴 수 있어요. 커뮤니티 공개 파일의 화면 1개를 정답으로 씀.
- D5 채점: Figma API로 받은 요소의 x·y·너비·높이·색·글자 크기 vs 만든 화면에서 Playwright로 잰 값. 위치 ±4px, 색 같은 값, 글자 크기 ±1px 안이면 맞음.
- D6: cursor-talk-to-figma-mcp는 Figma 플러그인 실행 + WebSocket 서버(`bun socket`)가 필요. "이 파일의 버튼 글자 20개를 한국어로 바꿔 줘" → Figma API로 다시 읽어 20개가 정확히 바뀌었나, 다른 노드를 건드렸나.

### ③ 코드 이해·검색

**사람들이 쓰는 상황 (출처)**
- Understand-Anything: "크고 낯선 코드"와 **온보딩**(프로젝트별 학습 순서)에서 가장 쓸모 있다고 함. 여러 언어로 된 데모(Online Boutique)를 분석하는 데 **약 30분, 토큰 약 20만 개**. 그래프는 한 시점의 사진이라 코드가 바뀌면 다시 만들어야 함 — Better Stack, 2026-07-29 ([링크](https://betterstack.com/community/guides/ai/understand-anything/))
- claude-context: 기본 검색은 글자가 같아야 찾는데, "사용자 권한 확인"처럼 **뜻으로** 찾고 싶을 때. Kubernetes 코드에서 같은 단어가 없는데도 관련 코드를 찾았고, 기본 검색은 비슷한 그림을 얻는 데 패턴을 5번쯤 바꿔야 했다고 함. **Ollama + 로컬 Milvus로 돈 안 들이고** 설치 — Medium, 2025-08-05 ([링크](https://medium.com/@jldavern/semantic-code-search-in-claude-code-the-missing-feature-32b22d62f6a2))

**U1. 온보딩 (형원 님 6-3b에 조건만 추가)**
- 6-3b T3(시작 파일 없이 "X는 어떻게 동작해?")의 정답표를 그대로 쓰고 조건에 Understand-Anything만 더함.
- 따로 기록: `/understand` **처음 분석에 든 토큰·시간**(한 번 드는 비용)과, 그 뒤 질문당 토큰. 처음 비용을 몇 번의 질문으로 나눠야 이득인지 계산할 수 있게.

**U2. 뜻으로 찾기 (정답 있음)**
- 6-3에서 "개념 찾기" 2문항은 Grep이 다 맞혔어요. 그래서 **질문과 코드에 같은 단어가 없게** 만들어야 해요. 예: 코드에는 `revokeSession`, `invalidateToken`만 있는데 "로그아웃하면 무엇이 지워져?"라고 묻기.
- 정답: 문항마다 정답 파일 2~4개를 사람이 미리 정함(형원 님 방식대로 Codex로 한 번 더 확인).
- 채점: 정답 파일을 몇 개 찾았나 + 토큰. 조건: 없음 / claude-context(Ollama `nomic-embed-text` + Milvus Docker).
- 주의: 기본 임베딩 차원이 다른 모델과 안 맞으면 조용히 실패한다는 후기가 있어서, 색인이 됐는지 먼저 확인.

### ⑤ 백엔드·인프라

**사람들이 쓰는 상황 (출처)**
- 쿠버네티스 고장 원인 찾기: 로컬 kind 클러스터에 이미지 오류, init 컨테이너 실패, 없는 Secret, 메모리 초과(OOMKilled), 반복 재시작을 일부러 만들고 Claude Code로 원인과 고칠 순서를 찾게 함. "꽤 잘함", 운영자가 꼭 옆에 있어야 함 — Mirantis, 2025-12-17 ([링크](https://t0.mirantis.com/claude-k8s-triage/)) (MCP가 아니라 스킬로 한 시험)
- 다른 MCP 서버 후기: Helm 설정 중첩 오류, Service 선택자와 파드 라벨이 안 맞는 경우를 찾음. 진단은 읽기 권한(RBAC)만으로 충분하고, 고치는 건 사람이 승인해야 한다고 함 — PerfectScale, 2025-06 ([링크](https://www.perfectscale.io/blog/troubleshooting-kubernetes-with-ai-part-two-using-the-k8s-mcp-server))
- Supabase MCP: 테이블 묻기, SQL 실행, 마이그레이션 적용, 보안·성능 점검, 로그 보기, 타입 만들기. 공식 문서가 **읽기 전용, 프로젝트 한정, 운영 DB는 꼭 필요할 때만**을 권하고, 사용자 글에 숨긴 지시(프롬프트 주입)를 경고. 로컬 CLI용 주소(`localhost:54321/mcp`)가 있음 — Supabase 공식 문서 ([링크](https://supabase.com/docs/guides/ai-tools/mcp))

**K1. 쿠버네티스 고장 찾기 (정답 있음)**
- 준비: Docker + kind로 로컬 클러스터, 네임스페이스 `shop`에 고장 5개를 심음. 정답표 = 아래 5개.
  1. 이미지 태그 오타 → ImagePullBackOff 2. 없는 Secret 참조 → CreateContainerConfigError 3. 메모리 제한 16Mi → OOMKilled 4. init 컨테이너 명령 실패 5. Service 선택자와 파드 라벨 불일치 → 엔드포인트 없음(파드는 정상이라 찾기 어려움)
- 시킬 말 ①: "shop 네임스페이스가 안 돌아가. 원인을 찾아서 알려 줘." → 원인 5개 중 몇 개 맞혔나.
- 시킬 말 ②: "고쳐 줘." → 클러스터를 실제로 바꿨나(전후 `kubectl get -o yaml` 비교). dbhub 시험(6-1)처럼 **읽기 전용 모드에서 막히나**를 봄. 두 서버 모두 읽기 전용이 기본으로 꺼져 있어서 "기본 설정"과 "읽기 전용 켬"을 둘 다 돌림.
- 조건: 없음(kubectl 허용) / kubernetes-mcp-server / mcp-server-kubernetes. 계정·돈 필요 없음.

**S1. Supabase (확인 필요)**
- 로컬 Supabase CLI(Docker)로 계정 없이 MCP가 붙는지 먼저 확인. 안 되면 무료 등급 계정으로.
- 시킬 말: "`reservations` 테이블을 만들고, 자기 예약만 볼 수 있게 권한(RLS)을 걸어 줘."
- 채점(SQL로 자동): 테이블·열 존재, RLS 켜짐, 다른 사용자 예약이 안 보이는지 쿼리로 확인 + 읽기 전용 모드에서 지우기 요청이 막히나.

### ⑥ QA·테스트

**사람들이 쓰는 상황 (출처)**
- 자기 프로젝트 30일 커밋을 보니 "TDD로 해"라고 했는데 **기능 10개 중 6개는 테스트를 코드 뒤에** 씀. CLAUDE.md 규칙만으로는 10번 중 6번 무시, 파일 쓰기 전에 실패하는 테스트가 있는지 검사하는 **훅**을 넣었더니 10개 중 9개가 테스트 먼저 — DEV Community 후기 ([링크](https://dev.to/kenimo49/i-told-claude-code-to-do-tdd-it-wrote-the-test-after-the-code-6-out-of-10-times-31kd), 직접 만든 훅이고 tdd-guard는 아님, 연도 표시 없음)

**T1. 테스트 먼저 쓰게 하기 (정답 있음)**
- 준비: 작은 파이썬·타입스크립트 예제 저장소, 만들 기능 3개.
- 시킬 말: "TDD로 이 기능 3개를 만들어 줘."
- 채점(자동, 대화 기록의 도구 호출 순서): 기능마다 **테스트 파일을 먼저 썼나**(3점) + 마지막에 테스트 통과(3점) + 막힌 횟수·토큰·시간.
- 조건: 없음 / CLAUDE.md에 TDD 규칙 / superpowers(TDD 스킬) / tdd-guard. superpowers와 tdd-guard가 "지시 vs 강제"로 갈리는지 보는 시험.
- 주의: tdd-guard는 파일 쓰기마다 검증 모델이 돌아서 시간이 늘 수 있음. `ANTHROPIC_API_KEY`가 설정돼 있으면 구독 대신 API로 과금될 수 있다고 제작자가 경고 → 시험 때 환경변수 비우기.

## 3. 시험 못 하거나 조건이 붙는 도구 (화면에 "시험 못 함" 근거)

| 도구 | 막는 것 | 우리가 할 수 있는 것 | 출처 |
|---|---|---|---|
| open-code-review | 리뷰용 LLM의 **API 키**(유료 사용량) | 팀 키가 생기면 시험. 지금은 "시험 못 함(별도 API 키 필요)" | 비교표, README |
| claude-code-security-review (GitHub Action) | **Anthropic API 키**(유료) | Claude Code 명령은 기본 `/security-review`와 같아서 시험 3에서 이미 봄 | 비교표, PR #11 |
| mcp-toolbox의 클라우드 DB(BigQuery 등) | **Google Cloud 계정·결제** | SQLite 부분은 시험함(6-1b). 클라우드는 "시험 못 함" | 시험 6-1b |
| terraform-mcp-server의 HCP Terraform 기능 | **HashiCorp 계정·토큰** | Registry 부분은 시험함(6-8) | 시험 6-8 |
| claude-mem의 observer | **30일 무료 뒤 유료**(결제 수단 입력) | 기본 기능은 시험함(6-5) | 비교표 |
| caveman의 Auto(모델 자동 선택) | **계정 로그인** | 나머지 기능은 시험함 | 비교표 |
| Figma-Context-MCP / cursor-talk-to-figma-mcp | **Figma 계정**(무료 가능) + 토큰, talk-to-figma는 플러그인 실행 | 무료 계정을 만들면 D5·D6 가능. 공식 Figma MCP는 유료 좌석이라 우리 목록 밖 | LogRocket |
| supabase | 호스팅은 **Supabase 계정**(무료 등급 있음) | 로컬 CLI로 계정 없이 되는지 확인 필요 | Supabase 문서 |
| claude-context | 기본 설정은 **OpenAI 키 + Zilliz Cloud** | Ollama + 로컬 Milvus면 무료(U2) | Medium |
| taste-skill | 돈은 안 들지만 **한 번에 30~45분·토큰 수십만** | 반복 횟수를 줄여서 시험(D3) | README |
| gstack의 외부 리뷰(`/codex`) | **Codex 로그인** | 기본 기능은 시험함 | 비교표 |
| trailofbits 깊은 감사 | 막는 건 없지만, 정답이 있는 "전문 분야 감사 과제"(스마트 계약 등)를 만들기 어려움 | 공개된 취약점이 있는 예제(CTF·공개 CVE 코드)를 정답으로 쓰면 가능 | 시험 4 |

## 4. 추천 순서 (형원 님이 돌릴 때)

1. **바로 되고 결과가 추천을 가르는 것**: K1(읽기 전용이 dbhub처럼 차이를 만들지), T1(지시 vs 강제), D4(공식 shadcn MCP와 겹치는지)
2. **6-7 디자인 블라인드와 같이**: D1·D2·D3의 자동 채점
3. **설치만 하면 되는 것**: U1(6-3b에 조건 추가), U2(Ollama + Milvus)
4. **계정이 필요한 것**: D5·D6(Figma 무료 계정), S1

## 출처

- [Anthropic — Improving frontend design through Skills (2025-11-12)](https://claude.com/blog/improving-frontend-design-through-skills)
- [mejba.me — Impeccable Claude Code design skill](https://www.mejba.me/blog/impeccable-claude-code-design-skill)
- [LogRocket — Design to code with Figma MCP (2025-11)](https://blog.logrocket.com/ux-design/design-to-code-with-figma-mcp/)
- [Builder.io — Claude Code + Figma MCP server (2025-07-28)](https://www.builder.io/blog/claude-code-figma-mcp-server)
- [shadcn/ui — MCP Server 문서](https://ui.shadcn.com/docs/mcp)
- [Better Stack — Understand Anything (2026-07-29)](https://betterstack.com/community/guides/ai/understand-anything/)
- [Medium — Semantic code search in Claude Code (2025-08-05)](https://medium.com/@jldavern/semantic-code-search-in-claude-code-the-missing-feature-32b22d62f6a2)
- [Mirantis — Troubleshooting Kubernetes with AI agents (2025-12-17)](https://t0.mirantis.com/claude-k8s-triage/)
- [PerfectScale — Troubleshooting Kubernetes with AI, part 2 (2025-06)](https://www.perfectscale.io/blog/troubleshooting-kubernetes-with-ai-part-two-using-the-k8s-mcp-server)
- [Supabase — MCP Server 문서](https://supabase.com/docs/guides/ai-tools/mcp)
- [DEV Community — Claude Code가 TDD에서 테스트를 나중에 쓴 기록](https://dev.to/kenimo49/i-told-claude-code-to-do-tdd-it-wrote-the-test-after-the-code-6-out-of-10-times-31kd)
