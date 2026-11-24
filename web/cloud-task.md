# 작업 지시: 웹 화면 만들기 (React + Tailwind)

> 노형원(ROH) 담당 `web/` 작업을 Claude Code(클라우드 또는 로컬)가 이어서 하기 위한 지시서예요.
> **시작할 때마다 이 파일과 `web/PROGRESS.md`를 먼저 읽고, `PROGRESS.md`의 "다음 한 걸음"부터 이어서 하세요.**

## 목표
`web/wireframe/v2/index.html`(확정된 2번 디자인, 화면 11개)을 **React + Tailwind + Vite** 앱으로 옮긴다.
브라우저로 `web/wireframe/v2/index.html`을 열면 동작하는 정답 화면이 있다. 모양·문구·흐름을 그대로 따른다.

## 꼭 지킬 것
1. **기획을 바꾸지 않는다.** 판정 규칙, 추천 규칙, 화면 문구, 숫자는 와이어프레임과 `server/api-draft.md` 그대로. 애매하면 바꾸지 말고 `PROGRESS.md`의 "물어볼 것"에 적는다.
2. **`web/` 폴더만 고친다.** `docs/`, `judgment/`, `data/`, `server/`는 읽기만 한다. (저장소 `CLAUDE.md` 규칙)
3. **브랜치 `ROH-front`에서만 작업**하고 push한다. `main`·`ROH`에 push하지 않는다. PR은 만들지 않는다(형원이 확인 후 만든다).
4. **작은 단계마다 커밋하고 바로 push**한다(화면 하나, 기능 하나 단위). 커밋할 때 `web/PROGRESS.md`도 같이 고친다. 중간에 세션이 끊겨도 push된 데까지는 이어서 할 수 있어야 한다.
5. "안전하다/위험하다"를 단정하는 문구를 새로 만들지 않는다. 판정 없는 쌍은 "확인된 정보 없음".
6. 키·토큰을 파일에 쓰지 않는다.

## 만들 것
- 위치: `web/app/` (Vite 프로젝트).
- 라우팅: 와이어프레임의 해시 주소와 같은 화면
  - `home`, `start`, `browse/:categoryId`, `find`(검색 결과), `tool/:id`, `box`, `ask/1`, `ask/2`, `result`, `help`
- 색·간격: 와이어프레임 `<style>`의 `:root` 변수(라이트·다크)를 그대로 CSS 변수로 옮기고 Tailwind에서 쓴다. 글꼴 Pretendard.
- 와이어프레임의 점선 메모(`.ann`, "메모 숨기기" 버튼)와 "참고한 사이트"(`notes`) 화면은 **실제 앱에 넣지 않는다**. `web/app/README.md`에 "디자인 근거는 wireframe/v2 참고"라고 적는다.
- 데이터는 **`web/app/src/api.js` 한 파일에서만** 읽는다.
  - 함수 이름과 응답 모양은 `server/api-draft.md` 2장(API 6개)을 따른다.
  - 지금은 서버가 없으므로 `VITE_API_BASE`가 비어 있으면 `server/sample-data/entries.json`, `compat.json`을 복사한 `web/app/src/data/`에서 읽고, 같은 규칙으로 계산해 같은 모양을 돌려준다(로컬 모드).
  - 로컬 모드의 판정·추천 계산은 `web/wireframe/v2/logic.js`를 옮긴 것이다. 직접 시험 결과(caveman, rtk 주의 문구)는 `web/wireframe/v2/data.js`의 `tested` 배열을 `web/app/src/data/tested.json`으로 옮겨 쓴다.
  - 필드 이름 차이 주의: 와이어프레임 `tokens` = entries의 `always_on_tokens_est`, `stars`·`pushed_at`·`license` = `auto.*`.
  - 조건 값 차이 주의: 와이어프레임 `logs` = api-draft `big_logs`, 와이어프레임 `""`(잘 모르겠어요) = `unknown`, shell은 `env.shell`.
- 도구함은 sessionStorage(`inv-box`), 조건 답은 sessionStorage(`inv-ans`). 서버로 보내지 않는다.

## 다 됐는지 확인하는 법
- `cd web/app && npm install && npm run build`가 오류 없이 끝난다.
- `npm test`(vitest): 로컬 모드 계산 시험이 통과한다. 최소 이것들:
  - 도구함 [superpowers, ecc, caveman] → 겹침 1쌍(superpowers×ecc), 빼기 후보 ecc(처음 읽는 양 9,169)
  - 조건 shell=powershell → rtk 더하기 카드에 PowerShell 주의 문구가 붙고 "지금 환경에서는 효과가 없어요"
  - 판정 없는 쌍은 `no_info`이고 화면 문구는 "확인된 정보 없음"
- 와이어프레임과 같은 흐름이 된다: 홈 검색 → 담기 → 도구함 → 질문 1 → 질문 2 → 결과. 질문에서 아무것도 안 고르고 다음을 누르면 안내 문구가 뜬다.
- 휴대폰 폭(390px)에서 가로로 넘치지 않는다.

## 범위 밖 (하지 말 것)
- 서버(Spring) 만들기: `server/cloud-task.md`가 따로 있다.
- 미저장 쌍 AI 판정 화면 상태(`ai_pending`, `ai_estimate`, `failed`): 문구 자리만 만들고 실제 호출은 하지 않는다.
- 기획안 9장 "결정 필요" 항목(위험 표시 방식 등)을 정하는 일.
