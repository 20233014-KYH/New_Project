#!/usr/bin/env python3
"""
1차 스캔(signals.jsonl) + MCP 도구 목록(mcp_tools.json) + 코드·문서 확인 사실을
도구 × 접근 범위 6칸 표로 묶는다. 결과: access_scope.json (웹 데이터), access_scope.md (검토용)

근거 종류
  검사       스캐너가 코드에서 찾음 (사람 라벨 전)
  코드 확인   Claude가 해당 코드를 직접 읽고 확인 (파일:줄 첨부)
  문서       제작자 문서
  실측(팀)    팀 실측 기록
칸 상태
  찾음 / 검사에서 찾지 못함 / 검사 전 / 해당 없음
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scanner import TOOLS  # noqa: E402
from build_xlsx import AI_NOTES  # noqa: E402  (판정을 끌어올린 신호의 AI 예비 판단)

COLS = ["내 파일", "설정 바꾸기", "명령 실행", "밖으로 보내기", "DB·외부 서비스", "브라우저"]
SCANNED_BY = {"내 파일": "R3·R5", "설정 바꾸기": "R9", "명령 실행": "R1·R2",
              "밖으로 보내기": "R4", "DB·외부 서비스": "R7", "브라우저": "R7"}

out_dir = Path(sys.argv[1])
repos_dir = Path(sys.argv[2])
S = [json.loads(l) for l in open(out_dir / "signals.jsonl", encoding="utf-8")]
M = json.load(open(out_dir / "mcp_tools.json", encoding="utf-8"))
commits = json.load(open(out_dir / "commits.json", encoding="utf-8"))


def ai_verdict(s):
    key = f"{s['sub']} {s['file']} {s['snippet']} {s['detail']}"
    for tool_rx, rule, rx, verdict, why in AI_NOTES:
        if re.fullmatch(tool_rx, s["tool"]) and s["rule"] == rule and re.search(rx, key):
            return verdict
    return ""


def ref(s):
    return f"{s['file']}:{s['line']}" if s.get("line") else s["file"]


table = {f: {c: dict(status=None, facts=[], notes=[]) for c in COLS} for f in TOOLS}


# 근거 종류. 저장소 CLAUDE.md의 calc/doc/tested/ai에 맞추되, 김용현 의견(PR #12)대로 calc는 "정확히 센 값"에만 씀.
# - 프로그램이 셈: 설정 파일(JSON)을 읽어 정확히 센 값 (지금은 R2 훅만) → calc
# - 프로그램이 찾음(글자 패턴): 정규식·이름 규칙으로 찾은 것. 놓치거나 잘못 잡을 수 있음 → pattern (사람 확인 전)
# - 코드 확인: Claude가 코드를 읽고 확인 → 사람 검수 전까지 ai
COUNT = "프로그램이 셈"
PATTERN = "프로그램이 찾음(글자 패턴)"
EVIDENCE_CODE = {COUNT: "calc", PATTERN: "pattern", "코드 확인": "ai", "문서": "doc", "실측(팀)": "tested"}


def fact(folder, col, text, when, evidence, refs=(), confirm=None):
    table[folder][col]["facts"].append(dict(text=text, when=when, evidence=evidence,
                                            evidence_code=EVIDENCE_CODE[evidence], reviewed=False, refs=list(refs)[:5],
                                            **({"confirm": confirm} if confirm else {})))


# ---------------------------------------------------------------------------
# 1) 스캐너 신호 → 칸
# ---------------------------------------------------------------------------
by = defaultdict(list)
for s in S:
    if s["counted"]:
        by[(s["tool"], s["rule"], s["sub"])].append(s)

for (folder, rule, sub), sigs in by.items():
    kept = [s for s in sigs if not ai_verdict(s).startswith("오탐")]
    dropped = len(sigs) - len(kept)
    if rule == "R1" and sub == "pipe-to-shell":
        hosts = defaultdict(list)
        for s in kept:
            m = re.search(r"https?://([^/\s'\"]+)(/[^\s'\"|)]*)?", s["snippet"])
            url = (m.group(1) + (m.group(2) or "")) if m else "?"
            hosts[(s["detail"].split("·")[-1].strip(), url)].append(s)
        by_host = defaultdict(lambda: dict(urls=set(), sigs=[]))
        for (host, url), ss in hosts.items():
            by_host[host]["urls"].add(url)
            by_host[host]["sigs"] += ss
        for host, v in by_host.items():
            owner = any("소유자" in a for s in v["sigs"] for a in s["adjust"])
            official = any("공식 설치기" in a for s in v["sigs"] for a in s["adjust"])
            src = "저장소 소유자 도메인" if owner else ("제3자 공식 설치기" if official else "출처 확인 필요")
            where = sorted({s["context"] for s in v["sigs"]})
            fact(folder, "명령 실행",
                 f"설치 안내가 원격 스크립트를 내려받아 셸로 바로 실행 ({host}, {src}) · 서로 다른 명령 {len(v['urls'])}개, "
                 f"신호 {len(v['sigs'])}건({'/'.join({'install':'설치 경로','docs':'문서','code':'코드','hook':'훅'}.get(w,w) for w in where)})",
                 "설치", PATTERN, [ref(s) for s in v["sigs"]])
        if dropped:
            table[folder]["명령 실행"]["notes"].append(
                f"원격 실행 형태 {dropped}건은 다른 도구 설치 안내 데이터 등으로 보여 사실에서 뺌(사람 확인 전)")
    elif rule == "R1" and sub == "exec-pipe":
        for s in kept:
            fact(folder, "명령 실행", "업데이트 명령이 원격 설치 스크립트를 내려받아 셸로 바로 실행 (저장소 소유자 도메인)",
                 s.get("when", "사용"), PATTERN, [ref(s)])
    elif rule == "R2":
        events = defaultdict(int)
        for s in kept:
            ev = s["detail"].split(" ")[0]
            events[ev] += 1
        freq = "·".join(f"{e} {n}" for e, n in sorted(events.items(), key=lambda x: -x[1]))
        inline = any("인라인 코드 실행" in s["detail"] for s in kept)
        fact(folder, "명령 실행",
             f"플러그인 훅 {len(kept)}개가 자동 실행 ({freq})" + (" · 훅마다 node -e 인라인 코드로 스크립트 위치를 찾은 뒤 실행" if inline else
                                                         " · 저장소 안의 고정 스크립트 실행"),
             "사용", COUNT, [ref(s) for s in kept])
    elif rule == "R9":
        label = {"perm-allow": "자동 허용 권한(permissions.allow)에 자기 도구 등록",
                 "mcp-config": "MCP 서버 설정(~/.claude.json·.mcp.json) 수정",
                 "instr-file": "CLAUDE.md 등 에이전트 지시 파일에 내용 추가",
                 "settings-hooks": "settings.json에 훅 등록"}[sub]
        glob = any("전역" in a for s in kept for a in s["adjust"])
        conf = "사람 확인 필요: 설치 경로에서 실제로 쓰는지" if all(s["severity"] == "low" for s in kept) else None
        fact(folder, "설정 바꾸기", f"{label}{' (전역 설정)' if glob else ' (프로젝트 설정)'}",
             "설치", PATTERN, [ref(s) for s in kept], conf)
        if sub == "settings-hooks":
            fact(folder, "명령 실행", "설치기가 settings.json에 등록한 훅이 이후 자동 실행", "사용", PATTERN,
                 [ref(s) for s in kept], conf)
    elif rule == "R3" and sub == "envkey":
        names = set()
        cred_sigs = []
        for s in kept:
            found = {n for n in re.findall(r"\b([A-Z][A-Z0-9_]*(?:TOKEN|SECRET|API_KEY|APIKEY|PASSWORD|PASSWD|PRIVATE_KEY)[A-Z0-9_]*)\b",
                                           s["snippet"])
                     if not re.search(r"TOKENS\b|_TOKENS_|M(?:IN|AX)_TOKEN", n)}  # 토큰 "개수" 설정은 자격 증명이 아님
            if found:
                names |= found
                cred_sigs.append(s)
        if not cred_sigs:
            table[folder]["내 파일"]["notes"].append(
                f"TOKEN이 들어간 환경변수 {len(kept)}곳은 토큰 개수 설정 등으로 보여 사실에서 뺌")
            continue
        kept = cred_sigs
        shown = ", ".join(sorted(names)[:6]) + (" 외" if len(names) > 6 else "")
        dev_only = all(re.match(r"(scripts|tools|docker|ci|\.github|bench\w*)/", s["file"]) for s in kept)
        fact(folder, "내 파일", f"토큰·키 환경변수를 읽음 ({shown or '이름은 코드 참조'}) · {len(kept)}곳",
             "사용", PATTERN, [ref(s) for s in kept],
             "사람 확인 필요: 모두 개발용 스크립트 위치라 사용자 실행 경로인지" if dev_only else None)
    elif rule == "R3":
        prot = [s for s in kept if any("차단·제외" in a for a in s["adjust"])]
        real = [s for s in kept if s not in prot]
        if real:
            lab = sigs[0]["detail"]
            fact(folder, "내 파일", f"{lab}에 접근하는 코드 {len(real)}곳", "사용", PATTERN, [ref(s) for s in real],
                 "사람 확인 필요: 실제로 읽는지, 보호 목록인지")
        n = len(prot) + dropped
        if n:
            table[folder]["내 파일"]["notes"].append(
                f"민감 경로 언급 {n}건은 차단·제외 목록으로 보여 사실에서 뺌(사람 확인 전)")
    elif rule == "R5":
        fact(folder, "내 파일", f"{sigs[0]['detail']} {len(kept)}곳", "사용", PATTERN, [ref(s) for s in kept])

# ---------------------------------------------------------------------------
# 2) MCP 도구 목록(R7) → DB·외부 / 브라우저 / 내 파일
# ---------------------------------------------------------------------------
for folder, r in M.items():
    if folder not in table or not r["tools"]:
        continue
    tools = r["tools"]
    kind = r["kind"]
    if r.get("tool_count") and kind == "db" and any(t.get("toolset") for t in tools):
        sets = sorted({t["toolset"] for t in tools})
        full = sorted({t["toolset"] for t in tools if "임의 SQL 실행" in t["caps"]})
        ro = sorted({t["toolset"] for t in tools if "SQL 실행(읽기 전용)" in t["caps"]})
        fact(folder, "DB·외부 서비스",
             f"미리 만든 설정(--prebuilt) {len(sets)}종, 도구 {len(tools)}개. 그중 {len(full)}종이 임의 SQL 실행 도구(execute_sql) 포함, "
             f"{len(ro)}종은 읽기 전용 SQL만", "사용", PATTERN,
             ["internal/prebuiltconfigs/tools/*.yaml"])
        continue
    exp = [t for t in tools if t["exposed"]]
    gated = [t for t in tools if t["exposed"] is False]

    def names(caps, pool):
        return [t["name"] for t in pool if set(t["caps"]) & caps]

    col = "브라우저" if kind == "browser" else "DB·외부 서비스"
    hi_caps = {"임의 코드 실행", "임의 SQL 실행", "쿠키·저장소 접근", "네트워크 가로채기", "페이지 제공 도구 실행",
               "확장 프로그램 설치·실행", "외부 서비스 조회(GitHub PR)"}
    caps_on = defaultdict(list)
    for t in exp:
        for c in t["caps"]:
            caps_on[c].append(t["name"])
    summary = ", ".join(f"{c} {len(v)}" for c, v in sorted(caps_on.items(), key=lambda x: -len(x[1])))
    head = f"MCP 도구 {len(tools)}개 추출, 기본 설정에서 {len(exp)}개 노출 ({summary})"
    if kind not in {"browser", "db"}:
        col = "DB·외부 서비스" if caps_on.get("외부 서비스 조회(GitHub PR)") else None
        if col is None:
            table[folder]["DB·외부 서비스"]["notes"].append(
                f"MCP 도구 {len(tools)}개는 모두 자기 데이터 조회({', '.join(t['name'] for t in tools[:4])} 등) · "
                "외부 DB·서비스 연결 도구는 찾지 못함")
            continue
    fact(folder, col, head, "사용", PATTERN, sorted({t["file"] for t in tools})[:3])
    for c in sorted(hi_caps):
        on = names({c}, exp)
        off = [(t["name"], t["exposed_why"]) for t in gated if c in t["caps"]]
        if on:
            fact(folder, col, f"기본 노출: {c} — {', '.join(on[:6])}{' 외' if len(on) > 6 else ''}", "사용", PATTERN,
                 sorted({f"{t['file']}:{t['line']}" for t in exp if c in t['caps']})[:3])
        if off:
            why = sorted({w for _, w in off})
            fact(folder, col, f"옵션을 켜야 노출: {c} {len(off)}개 ({'; '.join(why)})", "사용", PATTERN,
                 sorted({f"{t['file']}:{t['line']}" for t in gated if c in t['caps']})[:2])
    up = names({"파일 올리기·저장"}, exp)
    if up:
        fact(folder, "내 파일", f"MCP 도구로 내 파일을 페이지에 올리거나 결과를 파일로 저장 ({', '.join(up[:4])})", "사용", PATTERN,
             sorted({f"{t['file']}:{t['line']}" for t in exp if t['name'] in up})[:3])

# ---------------------------------------------------------------------------
# 3) 코드·문서로 확인한 사실 (스캐너 밖, 파일:줄 근거)
# ---------------------------------------------------------------------------
MANUAL = [
    ("colbymchenry_codegraph", "명령 실행", "Windows 업데이트는 소스 안의 PowerShell 스크립트를 base64로 인코딩해 실행정책 우회(-ExecutionPolicy Bypass)로 실행. 인코딩은 따옴표 깨짐 회피용이라고 주석에 명시", "업데이트", "코드 확인", ["src/upgrade/index.ts:829"]),
    ("colbymchenry_codegraph", "밖으로 보내기", "익명 사용 통계를 기본으로 보냄(설치기에서 기본 켜짐). 끄기: codegraph telemetry off, CODEGRAPH_TELEMETRY=0, DO_NOT_TRACK=1", "사용", "문서", ["TELEMETRY.md"]),
    ("colbymchenry_codegraph", "밖으로 보내기", "MCP 서버가 하루 한 번 GitHub에서 새 버전 확인(버전 번호만 받음). 끄기: CODEGRAPH_NO_UPDATE_CHECK=1", "사용", "문서", ["TELEMETRY.md"]),
    ("colbymchenry_codegraph", "밖으로 보내기", "사용 기록 대기열 파일 생성 관찰", "사용", "실측(팀)", ["judgment/review/2026-10-18-measure36/side_effects.md"]),
    ("bytebase_dbhub", "DB·외부 서비스", "--readonly 플래그는 1.5.0에서 제거됨(쓰면 오류로 종료). 읽기 전용은 dbhub.toml의 [[tools]] readonly = true로 설정", "사용", "코드 확인", ["src/config/env.ts:30"]),
    ("bytebase_dbhub", "DB·외부 서비스", "Claude Code 플러그인으로 설치하면 기본이 읽기 전용(readonly = true, 최대 1000행), 버전 1.5.0 고정", "설치", "코드 확인", ["plugin/dbhub.toml", "plugin/.mcp.json"]),
    ("bytebase_dbhub", "DB·외부 서비스", "설정 파일 없이 연결 문자열만 주면 execute_sql이 읽기 전용이 아님(수정·삭제 가능)", "사용", "코드 확인", ["src/utils/tool-metadata.ts:166", "src/utils/sql-access-policy.ts:74"]),
    ("microsoft_playwright-mcp", "브라우저", "browser_run_code_unsafe가 기본 노출. 제작자 설명: 'Playwright 서버 프로세스에서 임의 JavaScript 실행, 원격 코드 실행과 같음'", "사용", "코드 확인", ["playwright-core 1.64.0-alpha lib/coreBundle.js:69192"]),
    ("microsoft_playwright-mcp", "내 파일", "파일 접근은 기본적으로 작업 폴더 안으로 제한. --allow-unrestricted-file-access로 해제", "사용", "코드 확인", ["playwright-core lib/coreBundle.js:75566"]),
    ("microsoft_playwright-mcp", "브라우저", "--extension을 쓰면 실행 중인 내 브라우저(로그인 상태 포함)에 연결. --allowed-origins는 제작자가 '보안 경계가 아님'이라고 명시", "사용", "코드 확인", ["playwright-core lib/coreBundle.js:75566"]),
    ("ChromeDevTools_chrome-devtools-mcp", "밖으로 보내기", "사용 통계를 기본으로 Google에 보냄(usageStatistics 기본값 true). 끄기: --no-usage-statistics 또는 CHROME_DEVTOOLS_MCP_NO_USAGE_STATISTICS", "사용", "코드 확인", ["src/config/mcp-options.ts:194"]),
    ("ChromeDevTools_chrome-devtools-mcp", "브라우저", "evaluate_script(페이지 안 임의 JavaScript)가 기본 켜짐. --javascriptEvaluation=false로 끌 수 있으나 제작자는 '샌드박스가 아님'이라고 명시", "사용", "코드 확인", ["src/config/mcp-options.ts:200"]),
    ("ChromeDevTools_chrome-devtools-mcp", "브라우저", "autoConnect·browserUrl로 이미 열린 브라우저에 연결 가능. 공식 문서는 로그인된 세션에 연결하면 사용자 대신 행동할 수 있다고 경고", "사용", "문서", ["developer.chrome.com/docs/devtools/agents/get-started"]),
    ("Graphify-Labs_graphify", "밖으로 보내기", "문서·논문·이미지는 Claude로 보내 개념 추출(코드는 로컬 처리)", "사용", "문서", ["claudelog.com/claude-code-mcps/graphify"]),
    ("Graphify-Labs_graphify", "DB·외부 서비스", "MCP 도구 list_prs 등은 사용자의 gh CLI 로그인으로 GitHub PR 정보를 읽음", "사용", "코드 확인", ["graphify/prs.py:144"]),
    ("affaan-m_ECC", "DB·외부 서비스", "저장소 루트 .mcp.json에 chrome-devtools-mcp@1.10.1 설정이 있으나 plugin.json의 mcpServers는 비어 있음. 플러그인 설치 시 등록되는지는 실측 필요", "설치", "코드 확인", [".mcp.json", ".claude-plugin/plugin.json:39"]),
    ("JuliusBrussee_caveman", "밖으로 보내기", "범용 설치기는 기본으로 caveman-shrink MCP 프록시를 등록(--minimal로 생략). 프록시가 무엇을 어디로 보내는지는 검사 전", "설치", "문서", ["github.com/JuliusBrussee/caveman README"]),
    ("bytebase_dbhub", "내 파일", "~/.ssh/config와 기본 키 파일(id_rsa 등)을 읽는 이유는 DB 접속용 SSH 터널 기능(설정한 경우에만)", "사용", "코드 확인", ["src/utils/ssh-config-parser.ts:15", "src/connectors/manager.ts:159"]),
    ("microsoft_playwright-mcp", "명령 실행", "MCP 도구 browser_run_code_unsafe로 내 컴퓨터의 Playwright 서버 프로세스에서 임의 코드를 실행할 수 있음(기본 노출)", "사용", "코드 확인", ["playwright-core 1.64.0-alpha lib/coreBundle.js:69192"]),
    ("rtk-ai_rtk", "명령 실행", "훅은 Bash 도구 호출에만 걸려 모든 셸 명령을 실행 전에 rtk 명령으로 바꿔 씀(Read·Grep·Glob 제외)", "사용", "문서", ["README.md"]),
]
for f, col, text, when, ev, refs in MANUAL:
    fact(f, col, text, when, ev, refs)

# ---------------------------------------------------------------------------
# 4) 칸 상태
# ---------------------------------------------------------------------------
for f, cols in table.items():
    is_mcp = bool(M.get(f, {}).get("tool_count"))
    for c, cell in cols.items():
        if cell["facts"]:
            cell["status"] = "찾음"
        elif c == "밖으로 보내기":
            cell["status"] = "검사 전"
        elif c in {"DB·외부 서비스", "브라우저"}:
            cell["status"] = "검사에서 찾지 못함" if is_mcp or c == "DB·외부 서비스" and cell["notes"] else "해당 없음(MCP 도구 없음)"
        else:
            cell["status"] = "검사에서 찾지 못함"

out = {
    "schema": "access-scope/v0",
    "generated": "2026-10-31",
    "evidence_kinds": EVIDENCE_CODE,
    "evidence_revised": "2026-11-08: 글자 패턴으로 찾은 결과를 calc에서 pattern으로 바꿈(PR #12 의견). 사실·상태는 그대로",
    "note": "도움말이며 보증이 아님. 찾지 못함은 없음이 아니다. reviewed=false는 사람 검수 전.",
    "statuses": ["찾음", "검사에서 찾지 못함", "검사 전", "해당 없음(MCP 도구 없음)"],
    "columns": COLS,
    "scanned_by": SCANNED_BY,
    "tools": [dict(no=TOOLS[f]["no"], id=f, name=TOOLS[f]["name"], checked=commits.get(f, {}), cells=table[f])
              for f in sorted(TOOLS, key=lambda x: TOOLS[x]["no"])],
}
json.dump(out, open(out_dir / "access_scope.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 검토용 마크다운
md = []
for t in out["tools"]:
    md.append(f"### {t['name']}  (확인: {t['checked'].get('commit','')} · {t['checked'].get('date','')})")
    for c in COLS:
        cell = t["cells"][c]
        md.append(f"- **{c}** [{cell['status']}]")
        for x in cell["facts"]:
            md.append(f"    - ({x['when']}) {x['text']} — {x['evidence']}"
                      + (", 사람 확인 전" if x["evidence_code"] == "pattern" else "")
                      + (f" · {x['confirm']}" if x.get("confirm") else ""))
        for n in cell["notes"]:
            md.append(f"    - 참고: {n}")
    md.append("")
open(out_dir / "access_scope.md", "w", encoding="utf-8").write("\n".join(md))
print("\n".join(md))
