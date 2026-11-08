"""스캔 결과(signals.jsonl)를 라벨링용 엑셀로 만든다."""
import json
import re
import sys
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from scanner import TOOLS  # noqa: E402

out_dir = sys.argv[1]
S = [json.loads(l) for l in open(f"{out_dir}/signals.jsonl", encoding="utf-8")]
SUMMARY = json.load(open(f"{out_dir}/summary.json", encoding="utf-8"))

# 종합 판정을 끌어올린 신호에 대한 AI 예비 판단 (사람 라벨이 아니다)
AI_NOTES = [
    (r"affaan-m_ECC", "R1", r"opencode\.ai", "오탐 가능성 높음",
     "OpenCode 이주 문서의 OpenCode 공식 설치기 안내. 공식 설치기 목록에 opencode.ai가 없어 high로 남음"),
    (r"JuliusBrussee_caveman", "R1", r"hermes-agent", "오탐 가능성 높음",
     "다른 에이전트 설치 명령을 '설치 안 됨' 안내 문구로 표시하는 데이터(index.ts의 hint). 실행 경로는 확인되지 않음"),
    (r"JuliusBrussee_caveman", "R3", r"compress\.py", "오탐",
     "민감 파일을 압축 대상에서 빼는 제외 패턴(SENSITIVE_PATH_COMPONENTS 등)"),
    (r"Graphify-Labs_graphify", "R3", r"detect\.py", "오탐",
     "_CREDENTIAL_STORE_DIRS: 그래프 생성 시 자격 증명 폴더를 건너뛰는 목록"),
    (r"colbymchenry_codegraph", "R3", r"utils\.ts", "오탐",
     "SENSITIVE_HOME_DIRS: 민감 경로 접근을 막는 보호 코드"),
    (r"colbymchenry_codegraph", "R9", r"perm-allow", "정탐",
     "installer/targets/claude.ts가 settings.permissions.allow에 CodeGraph 도구를 추가. 문서화된 자동 허용 기능"),
    (r"rtk-ai_rtk", "R9", r"settings-hooks|instr-file", "정탐",
     "rtk init -g가 ~/.claude/settings.json에 PreToolUse 훅을 등록하고 CLAUDE.md 블록을 관리"),
    (r"Graphify-Labs_graphify", "R9", r"settings-hooks|instr-file", "정탐",
     "graphify install이 CLAUDE.md에 스킬 등록 블록, settings.json에 PreToolUse 훅을 씀"),
    (r"rtk-ai_rtk|colbymchenry_codegraph|JuliusBrussee_caveman", "R1", r"raw\.githubusercontent|github\.com", "정탐(출처 공식)",
     "저장소 소유자 도메인의 curl | sh 설치기. 형태는 R1이 맞고 출처 신뢰로 한 단계 낮춤"),
    (r"Graphify-Labs_graphify", "R1", r"astral\.sh", "정탐(출처 공식)",
     "README(다국어)의 uv 공식 설치기 안내"),
    (r"affaan-m_ECC", "R2", r".", "정탐",
     "훅마다 node -e 인라인 부트스트랩으로 플러그인 루트를 찾은 뒤 저장소 안 스크립트 실행. 매 도구 호출·매 프롬프트에 걸림"),
]


def ai_note(s):
    key = f"{s['sub']} {s['file']} {s['snippet']} {s['detail']}"
    for tool_rx, rule, rx, verdict, why in AI_NOTES:
        if re.fullmatch(tool_rx, s["tool"]) and s["rule"] == rule and re.search(rx, key):
            return verdict, why
    return "", ""


SEV_KO = {"high": "high", "medium": "medium", "low": "low"}
CTX_KO = {"hook": "훅", "install": "설치 경로", "code": "코드", "docs": "문서", "test": "테스트",
          "instruction": "지시문"}

wb = Workbook()
FONT = "Arial"
thin = Side(style="thin", color="D0D0D0")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
head_fill = PatternFill("solid", fgColor="1F3A5F")
input_fill = PatternFill("solid", fgColor="FFF2CC")
sev_fill = {"high": PatternFill("solid", fgColor="F8D7DA"), "medium": PatternFill("solid", fgColor="FFF3CD"),
            "low": PatternFill("solid", fgColor="E2EFDA")}


def header(ws, row, cols, widths):
    for c, (name, w) in enumerate(zip(cols, widths), 1):
        cell = ws.cell(row=row, column=c, value=name)
        cell.font = Font(name=FONT, bold=True, color="FFFFFF")
        cell.fill = head_fill
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        cell.border = border
        ws.column_dimensions[get_column_letter(c)].width = w


# ---------------- 신호목록 (판정에 반영된 신호) ----------------
ws = wb.active
ws.title = "신호목록"
cols = ["ID", "No", "도구", "유형", "세부", "보정 후 심각도", "기본 심각도", "위치", "파일", "줄",
        "내용", "보정 내역", "코드 조각", "AI 예비 판단", "AI 근거", "사람 라벨", "확인 수준", "메모"]
widths = [7, 5, 30, 6, 14, 10, 9, 9, 46, 6, 40, 38, 60, 14, 50, 13, 18, 30]
header(ws, 1, cols, widths)
ws.freeze_panes = "D2"
counted = [s for s in S if s["counted"]]
order = {"high": 0, "medium": 1, "low": 2}
counted.sort(key=lambda s: (TOOLS[s["tool"]]["no"], order.get(s["severity"], 3), s["rule"], s["file"], s["line"]))
for r, s in enumerate(counted, 2):
    v, why = ai_note(s)
    row = [f"S{r-1:03d}", TOOLS[s["tool"]]["no"], TOOLS[s["tool"]]["name"], s["rule"], s["sub"],
           s["severity"], s["base"], CTX_KO.get(s["context"], s["context"]), s["file"], s["line"] or None,
           s["detail"], " / ".join(s["adjust"]), s["snippet"], v, why, None, None, None]
    for c, val in enumerate(row, 1):
        cell = ws.cell(row=r, column=c, value=val)
        cell.font = Font(name=FONT, size=10)
        cell.border = border
        cell.alignment = Alignment(vertical="top", wrap_text=c in (11, 12, 13, 15))
    ws.cell(row=r, column=6).fill = sev_fill.get(s["severity"], PatternFill())
    for c in (16, 17, 18):
        ws.cell(row=r, column=c).fill = input_fill
last = len(counted) + 1
ws.auto_filter.ref = f"A1:R{last}"
dv1 = DataValidation(type="list", formula1='"실제 문제,헛경보,판단 보류"', allow_blank=True)
dv2 = DataValidation(type="list", formula1='"실측 확인,실측 미발동,실측 반증,미실측"', allow_blank=True)
ws.add_data_validation(dv1)
ws.add_data_validation(dv2)
dv1.add(f"P2:P{last}")
dv2.add(f"Q2:Q{last}")

# ---------------- 참고신호 (주석·테스트·문서·범위 외) ----------------
wr = wb.create_sheet("참고신호")
rcols = ["No", "도구", "유형", "세부", "위치", "파일", "줄", "내용", "제외 사유", "코드 조각"]
header(wr, 1, rcols, [5, 30, 7, 14, 9, 46, 6, 40, 40, 70])
wr.freeze_panes = "C2"
refs = [s for s in S if not s["counted"]]
refs.sort(key=lambda s: (TOOLS[s["tool"]]["no"], s["rule"], s["file"], s["line"]))
for r, s in enumerate(refs, 2):
    reason = " / ".join(a for a in s["adjust"] if "참고" in a) or (
        "3단계(R8-b) 범위 외" if s["rule"] == "R8-b?" else f"{CTX_KO.get(s['context'], s['context'])} 위치")
    row = [TOOLS[s["tool"]]["no"], TOOLS[s["tool"]]["name"], s["rule"], s["sub"],
           CTX_KO.get(s["context"], s["context"]), s["file"], s["line"] or None, s["detail"], reason, s["snippet"]]
    for c, val in enumerate(row, 1):
        cell = wr.cell(row=r, column=c, value=val)
        cell.font = Font(name=FONT, size=10)
        cell.border = border
        cell.alignment = Alignment(vertical="top", wrap_text=c in (8, 9, 10))
wr.auto_filter.ref = f"A1:J{len(refs)+1}"

# ---------------- 요약 (신호목록에서 수식으로 집계) ----------------
sm = wb.create_sheet("요약", 0)
sm["A1"] = "1차 스캔 요약 (R1·R2·R3·R5·R9)"
sm["A1"].font = Font(name=FONT, bold=True, size=14)
sm["A2"] = "판정은 '신호목록' 시트의 보정 후 심각도를 수식으로 집계한다. 사람 라벨 열에 '헛경보'를 고르면 '라벨 반영 판정'이 다시 계산된다."
sm["A2"].font = Font(name=FONT, size=10, italic=True, color="555555")
scols = ["No", "도구", "스캐너 판정", "high", "medium", "low", "R1", "R2", "R3", "R5", "R9",
         "라벨 반영 판정", "헛경보 표시 수", "참고신호 수"]
header(sm, 4, scols, [5, 34, 12, 7, 8, 7, 6, 6, 6, 6, 6, 14, 12, 11])
N = f"신호목록!$C$2:$C${last}"
SEV = f"신호목록!$F$2:$F${last}"
RULE = f"신호목록!$D$2:$D${last}"
LAB = f"신호목록!$P$2:$P${last}"
for i, row in enumerate(SUMMARY, 5):
    nm = row["tool"]
    sm.cell(row=i, column=1, value=row["no"])
    sm.cell(row=i, column=2, value=nm)
    sm.cell(row=i, column=4, value=f'=COUNTIFS({N},$B{i},{SEV},"high")')
    sm.cell(row=i, column=5, value=f'=COUNTIFS({N},$B{i},{SEV},"medium")')
    sm.cell(row=i, column=6, value=f'=COUNTIFS({N},$B{i},{SEV},"low")')
    for c, rule in zip(range(7, 12), ["R1", "R2", "R3", "R5", "R9"]):
        sm.cell(row=i, column=c, value=f'=COUNTIFS({N},$B{i},{RULE},"{rule}")')
    sm.cell(row=i, column=3, value=f'=IF(D{i}>0,"주의",IF(E{i}>0,"보통","낮음"))')
    hi = f'COUNTIFS({N},$B{i},{SEV},"high",{LAB},"<>헛경보")'
    me = f'COUNTIFS({N},$B{i},{SEV},"medium",{LAB},"<>헛경보")'
    sm.cell(row=i, column=12, value=f'=IF({hi}>0,"주의",IF({me}>0,"보통","낮음"))')
    sm.cell(row=i, column=13, value=f'=COUNTIFS({N},$B{i},{LAB},"헛경보")')
    sm.cell(row=i, column=14, value=f'=COUNTIF(참고신호!$B$2:$B${len(refs)+1},$B{i})')
    for c in range(1, 15):
        cell = sm.cell(row=i, column=c)
        cell.font = Font(name=FONT, size=10, bold=c in (3, 12))
        cell.border = border
end = 4 + len(SUMMARY)
sm.cell(row=end + 1, column=2, value="합계").font = Font(name=FONT, bold=True)
for c in list(range(4, 12)) + [13, 14]:
    L = get_column_letter(c)
    cell = sm.cell(row=end + 1, column=c, value=f"=SUM({L}5:{L}{end})")
    cell.font = Font(name=FONT, bold=True)
    cell.border = border

notes = [
    "범례",
    "· 노란 칸(신호목록 P·Q·R열)이 사람이 채우는 칸이다. 사람 라벨: 실제 문제 / 헛경보 / 판단 보류. 확인 수준: 실측 확인 / 실측 미발동 / 실측 반증 / 미실측.",
    "· 예: S001 행에 '헛경보', '미실측'을 고르고 메모에 '공식 설치기 안내 문서'라고 적는다.",
    "· AI 예비 판단은 판정을 끌어올린 신호에 대해 Claude가 코드를 읽고 붙인 의견이다. 사람 라벨(정답)이 아니다.",
    "· 판정 규칙: 보정 후 high가 1개 이상이면 주의, high 없이 medium이 있으면 보통, 그 외 낮음. '낮음'은 안전하다는 뜻이 아니다.",
    "· 참고신호: 주석·테스트 코드·문서 속 언급, 셸 실행 없는 문자열, 지시문 속 위험 명령(3단계 R8-b 후보). 판정에 넣지 않는다.",
    "· 스캔 대상: 각 저장소 기본 브랜치 최신 커밋(2026-10-28, git clone --depth 1). 대상 코드는 설치·실행하지 않았다.",
]
for k, t in enumerate(notes):
    c = sm.cell(row=end + 3 + k, column=1, value=t)
    c.font = Font(name=FONT, size=10, bold=(k == 0))
sm.freeze_panes = "C5"

wb.save(f"{out_dir}/scan_labeling.xlsx")
print("saved", len(counted), len(refs))
