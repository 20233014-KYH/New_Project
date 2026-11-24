#!/usr/bin/env python3
"""
R7 입력 만들기: MCP 서버가 Claude에게 여는 도구 목록 추출기

- 저장소(와 필요하면 npm 배포본) 파일을 읽기만 한다. 서버를 실행해 tools/list 를 받는 방식이 아니다.
- 도구마다 이름·설명·주석(readOnlyHint 등)을 뽑고, 이름·설명으로 "할 수 있는 일"을 분류한다.
- 같은 결과가 R8(도구 설명 속 숨은 지시) 검사의 입력이 된다.

사용법
  python3 -I mcp_tools.py <repos_dir> <out_dir> [<tool_folder>=<extra_dir> ...]
  예: colbymchenry_codegraph 는 저장소만, microsoft_playwright-mcp 는 실제 도구 코드가
      playwright-core 패키지에 있으므로 extra 로 그 압축 해제 폴더를 넘긴다.
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "vendor", "third_party", "dist", "build", "out", ".venv",
             "__pycache__", "target", "coverage", "docs", "site", "website"}
TEST_HINT = re.compile(r"(^|/)(tests?|__tests__|spec|fixtures?|e2e|evals?|examples?|testdata|mocks?|benchmarks?)(/|$)|"
                       r"(_test\.go|\.test\.[cm]?[jt]sx?|\.spec\.[cm]?[jt]sx?)$", re.I)
CODE_EXT = {".ts", ".tsx", ".js", ".mjs", ".cjs", ".py", ".go"}
YAML_EXT = {".yaml", ".yml"}
MAX_BYTES = 6_000_000

TOOL_FILE_HINT = re.compile(r"registerTool|defineTool|defineTabTool|ListToolsRequestSchema|inputSchema|"
                            r"ToolDefinition|@mcp\.tool|server\.tool\(|mcp\.NewTool|AddTool\(|types\.Tool\(|list_tools")
NAME_RX = re.compile(r"""^\s*name\s*[:=]\s*['"]([a-z][a-z0-9_]{2,63})['"],?\s*$""")
DESC_RX = re.compile(r"""^\s*description\s*[:=]\s*\(?\s*(?:['"`]|f['"])(.+?)(?:['"`],?\s*$|$)""")
REG_RX = re.compile(r"""(?:registerTool|server\.tool|\.addTool|mcp\.NewTool)\(\s*['"]([a-z][a-z0-9_]{2,63})['"]""")
CONST_RX = re.compile(r"""\b(?:export\s+)?const\s+[A-Z0-9_]*TOOL[A-Z0-9_]*\s*=\s*['"]([a-z][a-z0-9_]{2,63})['"]""")
PY_DECO_RX = re.compile(r"@\w+\.tool\(")
PY_DEF_RX = re.compile(r"^\s*(?:async\s+)?def\s+([a-z_][a-z0-9_]*)\s*\(")

# 할 수 있는 일 분류: 도구 "이름" 토큰을 기준으로 하고, 설명은 강한 문구만 본다.
# (설명 전체를 키워드로 훑으면 "resource"의 rce, "tablespace"의 tab 같은 오탐이 많았다)
MCP_KIND = {"bytebase_dbhub": "db", "googleapis_mcp-toolbox": "db",
            "microsoft_playwright-mcp": "browser", "ChromeDevTools_chrome-devtools-mcp": "browser",
            "colbymchenry_codegraph": "code",
            # 2026-11-09 추가: 외부 서비스·클러스터에 연결하는 MCP는 db와 같이 "DB·외부 서비스" 칸으로
            "supabase_mcp": "db", "containers_kubernetes-mcp-server": "db", "Flux159_mcp-server-kubernetes": "db",
            "hashicorp_terraform-mcp-server": "db", "GLips_Figma-Context-MCP": "db", "grab_cursor-talk-to-figma-mcp": "db",
            "Jpisnice_shadcn-ui-mcp-server": "db", "upstash_context7": "db", "zilliztech_claude-context": "db",
            "garrytan_gstack": "browser"}
NAME_CAPS = [
    ("임의 코드 실행", re.compile(r"(^|_)(run_code|evaluate|eval|execute_script|exec|shell|bash|run_command)(_|$)")),
    ("SQL 실행(읽기 전용)", re.compile(r"(^|_)(execute_sql|run_query|query)_?read_?only(_|$)|readonly_sql")),
    ("임의 SQL 실행", re.compile(r"(^|_)(execute_sql|run_query|execute_query|run_sql)(_|$)")),
    ("페이지 제공 도구 실행", re.compile(r"execute_[a-z0-9_]*tool")),
    ("확장 프로그램 설치·실행", re.compile(r"(install|uninstall|trigger|reload)_extension")),
    ("쿠키·저장소 접근", re.compile(r"cookie|localstorage|sessionstorage|storage(_|$)")),
    ("네트워크 가로채기", re.compile(r"(^|_)(route|unroute|network_state_set|intercept)(_|$)")),
    ("파일 올리기·저장", re.compile(r"upload|pdf|save|screencast|download|drop(_|$)")),
    ("브라우저 조작", re.compile(r"(^|_)(navigate|goto|click|click_at|dblclick|type|type_text|fill|fill_form|press|"
                                r"press_key|press_sequentially|drag|hover|select|select_option|check|uncheck|dialog|"
                                r"handle_dialog|new_page|close|close_page|tabs?|resize|resize_page|mouse|keydown|keyup|"
                                r"reload|emulate|emulate_media|open|attach|back|forward)(_|$)")),
    ("코드 색인 읽기", re.compile(r"^codegraph_")),
    ("외부 서비스 조회(GitHub PR)", re.compile(r"(^|_)(prs?|pr_impact|github)(_|$)")),
]
DESC_CAPS = [
    ("임의 코드 실행", re.compile(r"arbitrary javascript|rce-equivalent|evaluate javascript|evaluates? a javascript", re.I)),
    ("임의 SQL 실행", re.compile(r"execute (?:a single )?sql statement|execute sql queries", re.I)),
]
READ_FALLBACK = {"db": "DB 구조·상태 읽기", "browser": "관찰(읽기)", "code": "코드 색인 읽기"}
HIGH_CAPS = {"임의 코드 실행", "임의 SQL 실행", "쿠키·저장소 접근", "네트워크 가로채기",
             "페이지 제공 도구 실행", "확장 프로그램 설치·실행"}

# 서버 실행 옵션 중 접근 범위를 좁히거나 넓히는 것
OPT_RX = re.compile(r"""['"`](--(?:read-?only|isolated|allowed-origins|blocked-origins|allow-unrestricted-file-access|
                    caps|extension|auto-?connect|browser-?url|ws-?endpoint|user-data-dir|max-rows|demo|
                    categ[a-z-]*|no-[a-z-]*|experimental-[a-z-]*|slim|headless|isolated-context))\b""", re.X | re.I)
OPT_KEY_RX = re.compile(r"""^\s*['"]?(readonly|readOnly|isolated|autoConnect|browserUrl|wsEndpoint|maxRows|
                        allowUnrestrictedFileAccess|userDataDir|categoryExtensions|experimentalVision)['"]?\s*:""", re.X)


def iter_files(root: Path):
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            p = Path(dp) / fn
            if p.suffix.lower() not in CODE_EXT | YAML_EXT or fn.endswith((".min.js", ".d.ts")):
                continue
            try:
                if p.stat().st_size > MAX_BYTES or p.is_symlink():
                    continue
            except OSError:
                continue
            yield p


def classify(name, desc, kind):
    caps = [label for label, rx in NAME_CAPS if rx.search(name)
            and not (kind == "db" and label in {"브라우저 조작", "쿠키·저장소 접근", "네트워크 가로채기"})]
    if "SQL 실행(읽기 전용)" in caps and "임의 SQL 실행" in caps:
        caps.remove("임의 SQL 실행")
    if not caps:
        caps = [label for label, rx in DESC_CAPS if desc and rx.search(desc)]
        if "임의 SQL 실행" in caps and desc and re.search(r"read-?only", desc, re.I):
            caps = ["SQL 실행(읽기 전용)"]
    if not caps:
        caps = [READ_FALLBACK.get(kind, "읽기·기타")]
    return caps


def extract(root: Path, label: str):
    tools = {}
    options = set()
    opt_defaults = {}

    def add(name, **kw):
        if name.split("/")[-1] in {"true", "false", "null", "none", "undefined"}:
            return
        cur = tools.get(name)
        if cur is None or (not cur.get("description") and kw.get("description")):
            tools[name] = dict(name=name, source=label, **kw)

    for p in iter_files(root):
        rel = str(p.relative_to(root))
        if TEST_HINT.search(rel):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = text.splitlines()

        if p.suffix.lower() in YAML_EXT:
            if "kind: tool" not in text:
                continue
            toolset = p.stem
            for block in re.split(r"^---\s*$", text, flags=re.M):
                if not re.search(r"^kind:\s*tool\s*$", block, re.M):
                    continue
                m = re.search(r"^name:\s*(\S+)", block, re.M)
                d = re.search(r"^description:\s*(.+)$", block, re.M)
                t = re.search(r"^type:\s*(\S+)", block, re.M)
                if m:
                    key = f"{toolset}/{m.group(1)}"
                    add(key, description=(d.group(1).strip() if d else ""), file=rel, line=0,
                        how="YAML 정의", toolset=toolset, impl=(t.group(1) if t else ""))
            continue

        # 실행 옵션
        for m in OPT_RX.finditer(text):
            options.add(m.group(1).lower())
        if re.search(r"cli|option|config|args|flag", rel, re.I):
            for ln in lines:
                m = OPT_KEY_RX.match(ln)
                if m:
                    options.add(m.group(1))

        # 상수로 이름만 정의(동적 등록) — 힌트 단어가 없는 상수 전용 파일도 본다
        for i, ln in enumerate(lines):
            m = CONST_RX.search(ln)
            if m:
                add(m.group(1), description="", file=rel, line=i + 1, how="이름 상수(동적 등록)")
        # 옵션 기본값 (예: mcp-options.ts 의 name: { type: 'boolean', default: true })
        if re.search(r"option|config|flag", rel, re.I):
            for i, ln in enumerate(lines):
                m = re.match(r"^\s*([A-Za-z]\w+):\s*\{\s*$", ln)
                if m and m.group(1) not in opt_defaults:
                    for j in range(i + 1, min(i + 7, len(lines))):
                        d = re.match(r"^\s*default:\s*(true|false)\b", lines[j])
                        if d:
                            opt_defaults[m.group(1)] = d.group(1) == "true"
                            break
        if not TOOL_FILE_HINT.search(text):
            continue
        # 1) 객체 리터럴: name 다음 8줄 안에 description
        for i, ln in enumerate(lines):
            m = NAME_RX.match(ln)
            if not m:
                continue
            desc = None
            for j in range(i + 1, min(i + 9, len(lines))):
                d = DESC_RX.match(lines[j])
                if d:
                    desc = d.group(1)
                    break
            if desc is None:
                continue
            # 이 도구 정의 블록만 본다: 바로 위 define…( 부터 다음 define…( 또는 다음 name: 직전까지
            start = i
            for k in range(i, max(-1, i - 10), -1):
                if re.search(r"define\w*Tool\(|registerTool\(|types\.Tool\(", lines[k]):
                    start = k
                    break
            end = min(len(lines), i + 40)
            for k in range(i + 1, end):
                if re.search(r"define\w*Tool\(|registerTool\(|types\.Tool\(", lines[k]) or NAME_RX.match(lines[k]):
                    end = k
                    break
            window = "\n".join(lines[start:end])
            ro = re.search(r"readOnlyHint:\s*(true|false|\w+)", window)
            ty = re.search(r"""\btype:\s*['"](readOnly|action|input|destructive)['"]""", window)
            cap = re.search(r"""capability:\s*['"]([\w-]+)['"]""", window)
            skill_only = bool(re.search(r"skillOnly:\s*true", window))
            cond = re.search(r"conditions:\s*\[([^\]]*)\]", window)
            cat = re.search(r"category:\s*ToolCategory\.(\w+)", window)
            add(m.group(1), description=desc[:300], file=rel, line=i + 1, how="객체 정의",
                readOnlyHint=(ro.group(1) if ro else None), type=(ty.group(1) if ty else None),
                capability=(cap.group(1) if cap else None), skillOnly=skill_only,
                conditions=(re.findall(r"['\"](\w+)['\"]", cond.group(1)) if cond else []),
                category=(cat.group(1) if cat else None))
        # 1-b) 생성자 형태: types.Tool( 다음 줄의 name="..."
        for i, ln in enumerate(lines):
            if re.search(r"\b(?:types\.)?Tool\(\s*$", ln):
                for j in range(i + 1, min(i + 4, len(lines))):
                    m2 = NAME_RX.match(lines[j])
                    if m2:
                        add(m2.group(1), description="", file=rel, line=j + 1, how="생성자 정의")
                        break
        # 2) 등록 함수에 이름을 바로 넘김
        for i, ln in enumerate(lines):
            for m in REG_RX.finditer(ln):
                add(m.group(1), description="", file=rel, line=i + 1, how="등록 호출")
        # 4) 파이썬 데코레이터
        for i, ln in enumerate(lines):
            if PY_DECO_RX.search(ln):
                for j in range(i + 1, min(i + 5, len(lines))):
                    d = PY_DEF_RX.match(lines[j])
                    if d:
                        add(d.group(1), description="", file=rel, line=j + 1, how="데코레이터")
                        break
    return list(tools.values()), sorted(options), opt_defaults


def exposure(t, opt_defaults):
    """기본 설정으로 Claude에게 노출되는지와 그 근거"""
    if t.get("skillOnly"):
        return False, "skillOnly(MCP 비노출)"
    if t.get("toolset"):
        return None, f"--prebuilt={t['toolset']} 선택 시 노출"
    if t.get("capability"):
        on = t["capability"].startswith("core")
        return on, ("core 그룹(기본 노출)" if on else f"--caps={t['capability']} 필요")
    for c in t.get("conditions") or []:
        if not opt_defaults.get(c, False):
            return False, f"--{c}=true 필요"
    cat = t.get("category")
    if cat and cat not in {"INPUT", "NAVIGATION", "EMULATION", "PERFORMANCE", "NETWORK", "DEBUGGING"}:
        key = "category" + cat.capitalize()
        if key in opt_defaults or cat == "EXTENSIONS":
            on = opt_defaults.get(key, False)
            return on, (f"{key} 기본값 켜짐" if on else f"--{key}=true 필요")
    if t.get("conditions"):
        return True, "조건 옵션 기본값 켜짐(" + ", ".join(t["conditions"]) + ")"
    return True, "제한 조건 없음(기본 노출로 봄)"


def bundled_mcp_configs(repo: Path):
    out = []
    for p in list(repo.rglob(".mcp.json")) + list(repo.rglob(".claude-plugin/plugin.json")):
        if any(x in SKIP_DIRS for x in p.parts):
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        servers = d.get("mcpServers") or {}
        if isinstance(servers, dict):
            for name, cfg in servers.items():
                cmd = " ".join([cfg.get("command", "")] + [str(a) for a in cfg.get("args", [])]) if isinstance(cfg, dict) else str(cfg)
                out.append(dict(file=str(p.relative_to(repo)), server=name, command=cmd[:200],
                                pinned=bool(re.search(r"@\d+\.\d+", cmd)), latest="@latest" in cmd))
    return out


def main():
    repos_dir, out_dir = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    extra = defaultdict(list)
    for arg in sys.argv[3:]:
        k, v = arg.split("=", 1)
        extra[k].append(Path(v).resolve())
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for repo in sorted(repos_dir.iterdir()):
        if not repo.is_dir():
            continue
        tools, opts, defaults = extract(repo, "저장소")
        for ex in extra.get(repo.name, []):
            t2, o2, d2 = extract(ex, f"npm:{ex.name}")
            # 배포본 번들에는 CLI 명령 정의도 섞여 있으므로 MCP 도구 표식(capability/type)이 있는 것만 쓴다
            t2 = [t for t in t2 if t.get("capability") or t.get("type")]
            names = {t["name"] for t in tools}
            tools += [t for t in t2 if t["name"] not in names]
            opts = sorted(set(opts) | set(o2))
            defaults = {**d2, **defaults}
        kind = MCP_KIND.get(repo.name, "other")
        for t in tools:
            t["caps"] = classify(t["name"].split("/")[-1], t.get("description"), kind)
            t["exposed"], t["exposed_why"] = exposure(t, defaults)
        opts = [o for o in opts if not re.match(r"--no-(?!usage)|--experimental-(?!vision)", o)]
        configs = bundled_mcp_configs(repo)
        cap_count = Counter(c for t in tools for c in t["caps"])
        cap_default = Counter(c for t in tools if t["exposed"] for c in t["caps"])
        keep_defaults = {k: v for k, v in defaults.items()
                         if re.search(r"readonly|isolated|usage|telemetry|javascript|file|categ|memory|vision|"
                                      r"devtools|slim|headless|autoConnect|interop", k, re.I)}
        result[repo.name] = dict(kind=kind, tool_count=len(tools), caps=dict(cap_count), caps_default=dict(cap_default),
                                 options=opts, option_defaults=keep_defaults, bundled_mcp=configs, tools=tools)
        print(f"{repo.name:38s} 도구 {len(tools):4d} (기본노출 {sum(1 for t in tools if t['exposed'])}) "
              f"{dict(cap_count.most_common(7))}")
    with open(out_dir / "mcp_tools.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
