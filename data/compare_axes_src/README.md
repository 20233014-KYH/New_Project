# compare_axes_v0 만드는 코드

`../compare_axes_v0.csv`(김용현에게 넘기는 표)와 `../compare_axes_v0.md`(읽기용)를 만듭니다.

| 파일 | 내용 |
|---|---|
| `rows_g1.py` ~ `rows_g6.py` | 분야 1~6의 도구별 조사 값(축 값·근거, 실행 방식, 다른 점, 이럴 때, 약한 점, 설치·비용, 출처). **사람이 고치는 곳은 여기** |
| `build_compare.py` | 위 값에 팀 실측(`measured_36.csv`), 접근 범위 표(`security/results/2026-11-09/access_scope.json`), 버전·라이선스를 붙여 CSV를 만듦 |
| `build_md.py` | CSV와 같은 내용을 분야별 읽기용 문서로 만듦 |

```bash
# 저장소 루트에서. repos/는 36개 저장소를 git clone --depth 1 한 폴더(소유자_저장소 이름)
python3 data/compare_axes_src/build_compare.py . data/security/results/2026-11-09 data repos
python3 data/compare_axes_src/build_md.py data/compare_axes_v0.md
```

## 칸 설명 (CSV)

- `축1~4_이름/값/근거`: PR #13 분야별 축. 근거는 `calc`(정확히 셈) / `doc`(문서·제작자 주장) / `tested`(팀이 직접 시험) / `ai`(우리가 정리) / `pattern`(프로그램이 글자 패턴으로 찾음, 사람 확인 전)
- `실행방식`: 자연어로 부탁하면 저절로 쓰이는지, 명령을 직접 불러야 하는지 (노형원 요청, PR #16)
- `다른점`: "같은 분야의 □□에 비해 …" 한 줄 / `이럴때`: 그 차이가 필요한 상황 한 줄 (김용현 요청, PR #12) / `약한점`. 셋 다 근거는 `ai`(`비교_근거` 칸)
- `처음읽는양_도구없음대비`, `더해진_*`, `MCP도구`, `첫응답_실행된훅`: 팀 실측 그대로. 에이전트는 기본 6개를 뺀 값. 작업 중 비용(쓸 때마다 도는 훅, MCP 호출 결과)은 들어 있지 않음
- `접근범위`: 6칸 상태(찾음 / 못 찾음 / 검사 전 / 해당 없음). "못 찾음"은 "없음"이 아님
- `사람확인`: 모두 `전`. 사람이 원문을 열어 확인하면 `후`로 바꿈
