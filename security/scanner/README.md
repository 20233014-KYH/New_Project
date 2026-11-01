# 위험도 스캐너 (v3, 2026-10-31)

Claude 도구 저장소의 파일을 **읽기만 해서** 위험 행동 신호와 접근 범위를 정리하는 스크립트입니다.
대상 도구를 설치하거나 실행하지 않습니다. 분류 기준은 [`../README.md`](../README.md)(위험 유형 분류 v2)입니다.

결과는 판결이 아니라 **신호**입니다. "찾지 못함"은 "없음"이 아니고, 모든 결과는 사람 검수 전입니다.

## 파일

| 파일 | 하는 일 | 다루는 유형 |
|---|---|---|
| `scanner.py` | 정규식·JSON 파싱으로 행동 신호를 찾음 | R1 원격 실행 설치, R2 훅, R3 민감 정보, R5 파괴적 작업, R9 설정·권한 변경 |
| `mcp_tools.py` | MCP 서버 코드에서 도구 이름·설명을 뽑고, 할 수 있는 일과 기본으로 켜지는지 판단 | R7 (결과의 도구 설명은 R8 입력으로도 씀) |
| `build_access.py` | 위 두 결과와 코드·문서로 확인한 사실을 도구 × 접근 범위 6칸 표로 묶음 | 웹 데이터 `access_scope.json` |
| `build_xlsx.py` | 사람 라벨링용 엑셀 시트 생성 | 정확도 측정용 |

## 실행 방법

Python 3 표준 라이브러리만 씁니다(엑셀 생성만 openpyxl 필요).

```bash
# 1) 대상 저장소 받기 (폴더 이름은 소유자_저장소)
git clone --depth 1 https://github.com/rtk-ai/rtk repos/rtk-ai_rtk

# playwright-mcp는 실제 도구 코드가 npm 배포본(playwright-core)에 있어서 따로 받음 (설치·실행 안 함)
npm pack playwright-core@<버전> && mkdir pw && tar -xzf playwright-core-*.tgz -C pw

# 2) 행동 신호
python3 -I security/scanner/scanner.py repos out

# 3) MCP 도구 목록
python3 -I security/scanner/mcp_tools.py repos out microsoft_playwright-mcp=pw/package

# 4) out/commits.json 에 저장소별 {"commit": ..., "date": ...} 를 적은 뒤 접근 범위 표
cd security/scanner && python3 build_access.py ../../out ../../repos

# 5) 라벨링 시트
python3 security/scanner/build_xlsx.py out
```

`-I`는 받은 저장소 안의 파이썬 파일이 실수로 불러와지지 않게 하는 옵션입니다.

## access_scope.json 구조

```
tools[] → cells[칸 이름] → {
  status: 찾음 | 검사에서 찾지 못함 | 검사 전 | 해당 없음(MCP 도구 없음),
  facts[]: { text, when(설치/사용/업데이트), evidence, evidence_code, reviewed, refs, confirm? },
  notes[]
}
```

- 칸 6개: 내 파일 / 설정 바꾸기 / 명령 실행 / 밖으로 보내기 / DB·외부 서비스 / 브라우저
- `evidence_code`는 CLAUDE.md의 근거 종류에 맞췄습니다: 검사 → `calc`, 문서 → `doc`, 팀 실측 → `tested`, 코드 확인(Claude가 코드를 읽고 확인) → `ai`
- `reviewed`는 모두 `false`입니다. 사람이 확인하면 `true`로 바꿉니다.
- `confirm`이 있는 줄은 "설치 경로에서 실제로 쓰는지" 같은 확인이 남은 것입니다.
- `build_access.py`의 `MANUAL` 목록은 스캐너 밖에서 코드·문서로 확인한 사실입니다(파일:줄 근거 포함).

## v3에서 바뀐 것

- **R1-b 추가**: 실행 함수(`run`·`spawn`·`exec` 등) 안에서 `… | sh`로 조립한 원격 실행을 잡습니다. 1회차가 놓친 codegraph `codegraph upgrade`(src/upgrade/index.ts:668)를 이제 탐지합니다.
- **R7 추출기 신규** (`mcp_tools.py`)
- **접근 범위 표 신규** (`build_access.py`)

## 알려진 한계

- 저장소 전체를 스캔해서, 서버·테스트 도구가 함께 든 모노레포는 사용자와 무관한 코드도 잡힙니다.
- MCP 도구 추출은 정의 형태가 다르면 놓칩니다(chrome-devtools 메모리 도구 일부). 서버를 실제로 띄워 `tools/list`와 비교해야 정확합니다.
- 할 수 있는 일은 도구 **이름** 기준으로 분류합니다. 이름과 실제 동작이 다르면 틀릴 수 있습니다.
- R4(밖으로 보내기)는 아직 규칙이 없습니다.
- 규칙을 이 12개 도구를 보며 다듬었으므로, 정확도는 새로 고른 도구로 재야 합니다.
