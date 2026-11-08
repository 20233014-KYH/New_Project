#!/usr/bin/env python3
"""
Claude 도구 위험도 스캐너 - 1차 범위 (R1, R2, R3, R5, R9)
기준 문서: "Claude 도구 위험 유형 분류 (심화) v2"

원칙
- 저장소 파일을 읽기만 한다. 대상 코드를 설치하거나 실행하지 않는다.
- 결과는 판결이 아니라 신호다. 종합 판정은 "확인한 위험 요소" 기준이다.

사용법
  python3 -I scanner.py <repos_dir> <out_dir>
  repos_dir 아래 폴더 이름은 "<owner>_<repo>" 형식이어야 한다.
"""
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. 도구 메타데이터 (목적 대조용 분류)
# ---------------------------------------------------------------------------
TOOLS = {
    "obra_superpowers":                     {"no": 1,  "name": "obra/superpowers",                  "cat": {"workflow"}},
    "affaan-m_ECC":                         {"no": 2,  "name": "affaan-m/ECC",                      "cat": {"workflow", "security"}},
    "JuliusBrussee_caveman":                {"no": 7,  "name": "JuliusBrussee/caveman",             "cat": {"token"}},
    "rtk-ai_rtk":                           {"no": 8,  "name": "rtk-ai/rtk",                        "cat": {"cli-proxy"}},
    "Graphify-Labs_graphify":               {"no": 13, "name": "Graphify-Labs/graphify",            "cat": {"code-index"}},
    "colbymchenry_codegraph":               {"no": 14, "name": "colbymchenry/codegraph",            "cat": {"code-index"}},
    "nextlevelbuilder_ui-ux-pro-max-skill": {"no": 19, "name": "nextlevelbuilder/ui-ux-pro-max-skill", "cat": {"design"}},
    "Leonxlnx_taste-skill":                 {"no": 20, "name": "Leonxlnx/taste-skill",              "cat": {"design"}},
    "bytebase_dbhub":                       {"no": 25, "name": "bytebase/dbhub",                    "cat": {"database"}},
    "googleapis_mcp-toolbox":               {"no": 26, "name": "googleapis/mcp-toolbox",            "cat": {"database", "cloud"}},
    "microsoft_playwright-mcp":             {"no": 31, "name": "microsoft/playwright-mcp",          "cat": {"browser"}},
    "ChromeDevTools_chrome-devtools-mcp":   {"no": 32, "name": "ChromeDevTools/chrome-devtools-mcp", "cat": {"browser"}},
}

# R3 목적 대조 허용표: 도구 분류 -> 접근이 설명과 맞는 민감 경로 종류
R3_ALLOW = {
    "database": {"dotenv", "envkey", "ssh"},  # DB 접속용 SSH 터널 기능
    "cloud":    {"aws", "gcloud", "dotenv", "envkey"},
    "browser":  {"browser"},
    "security": {"ssh", "aws", "gnupg", "dotenv", "browser", "gcloud"},  # 차단·검사 목적의 언급
    "cli-proxy": set(),
    "code-index": set(),
    "workflow": set(),
    "token": set(),
    "design": set(),
}

# R1 출처 신뢰: 저장소 소유자 외에 널리 쓰이는 공식 설치기 도메인
OFFICIAL_INSTALLERS = {
    "sh.rustup.rs", "astral.sh", "bun.sh", "deno.land", "get.docker.com",
    "raw.githubusercontent.com/nvm-sh", "raw.githubusercontent.com/homebrew",
    "install.python-poetry.org", "get.pnpm.io", "claude.ai", "cli.github.com",
}

# ---------------------------------------------------------------------------
# 2. 파일 선택
# ---------------------------------------------------------------------------
SKIP_DIRS = {".git", "node_modules", "vendor", "third_party", "dist", "build",
             "out", ".venv", "venv", "__pycache__", "target", ".next", "coverage"}
TEXT_EXT = {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".py", ".sh", ".bash",
            ".zsh", ".ps1", ".psm1", ".cmd", ".bat", ".rs", ".go", ".rb",
            ".json", ".toml", ".yaml", ".yml", ".md", ".mdx", ".txt", ""}
CODE_EXT = {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".py", ".sh", ".bash",
            ".zsh", ".ps1", ".psm1", ".cmd", ".bat", ".rs", ".go", ".rb", ""}
MAX_BYTES = 1_000_000

TEST_HINT = re.compile(r"(^|/)(tests?|__tests__|spec|specs|fixtures?|e2e|evals?|"
                       r"benchmarks?|examples?|testdata|mocks?)(/|$)", re.I)
DOCS_HINT = re.compile(r"(^|/)(docs?|site|website|blog|i18n|translations?)(/|$)", re.I)
TEST_FILE = re.compile(r"(_test\.go|\.test\.[cm]?[jt]sx?|\.spec\.[cm]?[jt]sx?|(^|/)test_[^/]*\.py|_test\.py|(^|/)tests?\.rs)$", re.I)
INSTRUCTION_FILE = re.compile(r"(^|/)(SKILL\.md|AGENTS\.md|CLAUDE\.md|GEMINI\.md)$|"
                              r"(^|/)(commands|agents|skills|rules)/.*\.md$", re.I)


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() not in TEXT_EXT:
                continue
            if fn.endswith((".min.js", "-lock.json", ".lock")) or fn == "package-lock.json":
                continue
            try:
                if p.stat().st_size > MAX_BYTES or p.is_symlink():
                    continue
            except OSError:
                continue
            yield p


def read_text(p: Path):
    try:
        b = p.read_bytes()
    except OSError:
        return None
    if b"\x00" in b[:4096]:
        return None
    return b.decode("utf-8", errors="replace")


def context_of(rel: str, hook_files: set):
    """파일 위치 분류: hook / install / test / instruction / docs / code"""
    if rel in hook_files:
        return "hook"
    name = rel.rsplit("/", 1)[-1].lower()
    if TEST_HINT.search(rel) or TEST_FILE.search(rel):
        return "test"
    if re.match(r"(readme|install)[^/]*\.(md|mdx|txt)$", name) or \
       re.match(r"install[^/]*\.(sh|ps1|cmd|bat)$", name) or name == "package.json":
        return "install"
    if INSTRUCTION_FILE.search(rel):
        return "instruction"
    if name.endswith((".md", ".mdx", ".txt")) or DOCS_HINT.search(rel):
        return "docs"
    return "code"


# ---------------------------------------------------------------------------
# 3. R2: 플러그인 훅 설정 찾기 + 훅 스크립트 추적
# ---------------------------------------------------------------------------
HOOK_EVENT_FREQ = {  # 노출 빈도 (높을수록 자주 실행)
    "PreToolUse": "매 도구 호출", "PostToolUse": "매 도구 호출",
    "PostToolUseFailure": "도구 실패 시", "UserPromptSubmit": "매 프롬프트",
    "SessionStart": "세션 시작", "SessionEnd": "세션 종료", "Stop": "응답 종료마다",
    "SubagentStart": "서브에이전트 시작", "SubagentStop": "서브에이전트 종료",
    "PreCompact": "컨텍스트 압축 전", "Notification": "알림 시",
}
SCRIPT_REF = re.compile(r"""([\w.${}/\\-]*?[\w-]+\.(?:js|mjs|cjs|ts|sh|py|ps1|cmd|bat))\b""")
R2_DANGER = [
    (re.compile(r"\bcurl\b|\bwget\b|\birm\b|Invoke-WebRequest"), "네트워크 다운로드"),
    (re.compile(r"\beval\b"), "eval"),
    (re.compile(r"\bbash\s+-c\b|\bsh\s+-c\b"), "셸 문자열 실행"),
    (re.compile(r"\bnode\s+-e\b|\bpython3?\s+-c\b"), "인라인 코드 실행"),
]


def find_plugin_roots(repo: Path):
    roots = set()
    for pj in repo.rglob(".claude-plugin/plugin.json"):
        if any(part in SKIP_DIRS for part in pj.parts):
            continue
        roots.add(pj.parent.parent)
    for mj in repo.rglob(".claude-plugin/marketplace.json"):
        if any(part in SKIP_DIRS for part in mj.parts):
            continue
        try:
            data = json.loads(mj.read_text(encoding="utf-8"))
        except Exception:
            continue
        for pl in data.get("plugins", []):
            src = pl.get("source")
            if isinstance(src, str) and src.startswith("."):
                cand = (mj.parent.parent / src).resolve()
                if cand.is_dir() and str(cand).startswith(str(repo.resolve())):
                    roots.add(cand)
    return roots


def load_hook_configs(repo: Path):
    """(설정 파일 상대경로, 플러그인 루트, hooks dict) 목록.
    플러그인: plugin.json의 hooks(객체 또는 경로) + 루트의 hooks/hooks.json
    프로젝트: .claude/settings.json 의 hooks"""
    out = []
    for root in find_plugin_roots(repo):
        pj = root / ".claude-plugin" / "plugin.json"
        try:
            pdata = json.loads(pj.read_text(encoding="utf-8")) if pj.exists() else {}
        except Exception:
            pdata = {}
        h = pdata.get("hooks")
        if isinstance(h, dict):
            out.append((str(pj.relative_to(repo)), root, h))
        elif isinstance(h, str):
            hp = (root / h).resolve()
            if hp.exists():
                try:
                    hd = json.loads(hp.read_text(encoding="utf-8"))
                    out.append((str(hp.relative_to(repo.resolve())), root, hd.get("hooks", hd)))
                except Exception:
                    pass
        hj = root / "hooks" / "hooks.json"
        if hj.exists():
            try:
                hd = json.loads(hj.read_text(encoding="utf-8"))
                out.append((str(hj.relative_to(repo)), root, hd.get("hooks", hd)))
            except Exception:
                pass
    for st in repo.rglob(".claude/settings*.json"):
        if any(part in SKIP_DIRS for part in st.parts):
            continue
        try:
            sd = json.loads(st.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(sd.get("hooks"), dict):
            out.append((str(st.relative_to(repo)), st.parent.parent, sd["hooks"]))
    # 같은 파일 중복 제거
    seen, uniq = set(), []
    for item in out:
        if item[0] not in seen:
            seen.add(item[0])
            uniq.append(item)
    return uniq


def resolve_script(ref: str, plugin_root: Path, repo: Path):
    ref = re.sub(r"^\$\{?\w+\}?[/\\]", "", ref.strip("\"'"))
    ref = ref.replace("\\", "/")
    for base in (plugin_root, repo):
        cand = (base / ref)
        if cand.is_file():
            return cand
    return None


def scan_hooks(repo: Path, signals: list, tool: str):
    hook_files = set()
    cfgs = load_hook_configs(repo)
    for cfg_rel, root, hooks in cfgs:
        for event, groups in hooks.items():
            if not isinstance(groups, list):
                continue
            for g in groups:
                matcher = g.get("matcher", "*") if isinstance(g, dict) else "*"
                for hk in (g.get("hooks", []) if isinstance(g, dict) else []):
                    cmd = hk.get("command", "")
                    if not cmd:
                        continue
                    flags = [label for rx, label in R2_DANGER if rx.search(cmd)]
                    scripts = []
                    for ref in SCRIPT_REF.findall(cmd):
                        sp = resolve_script(ref, root, repo)
                        if sp:
                            rel = str(sp.relative_to(repo))
                            scripts.append(rel)
                            hook_files.add(rel)
                            for sib in sp.parent.iterdir():  # 같은 폴더의 보조 스크립트
                                if sib.is_file() and sib.suffix.lower() in CODE_EXT:
                                    hook_files.add(str(sib.relative_to(repo)))
                    takes_input = bool(re.search(r"\$\{?(PROMPT|INPUT|TOOL_INPUT|ARGUMENTS)\}?|\$1\b|\$@", cmd))
                    if takes_input:
                        sev, adj = "high", ["외부 입력을 셸에 전달 +1"]
                    elif flags:
                        sev, adj = "medium", []
                    else:
                        sev, adj = "low", ["저장소 안의 고정 스크립트 실행 -1"]
                    signals.append(dict(
                        tool=tool, rule="R2", sub="hook", file=cfg_rel, line=0,
                        context="hook", base="medium", severity=sev, adjust=adj,
                        detail=f"{event} [{matcher}] ({HOOK_EVENT_FREQ.get(event, event)})"
                               + (f" · {', '.join(flags)}" if flags else "")
                               + (f" · 스크립트: {', '.join(scripts[:3])}" if scripts else ""),
                        snippet=cmd[:160] + ("…" if len(cmd) > 160 else ""),
                        counted=True))
    return hook_files, len(cfgs)


# ---------------------------------------------------------------------------
# 4. 줄 단위 규칙 (R1, R3, R5) 과 파일 단위 규칙 (R9)
# ---------------------------------------------------------------------------
R1_PATTERNS = [
    re.compile(r"(?:curl|wget)\b[^\n|;]*?(https?://[^\s'\"|)]+)[^\n|]*\|\s*(?:sudo\s+)?(?:-?\w+=\S+\s+)?(?:ba|z)?sh\b"),
    re.compile(r"(?:irm|iwr|Invoke-RestMethod|Invoke-WebRequest)\b[^\n|]*?(https?://[^\s'\"|)]+)[^\n|]*\|\s*(?:iex|Invoke-Expression)\b", re.I),
    re.compile(r"(?:ba|z)?sh\s*<\(\s*(?:curl|wget)\b[^\n)]*?(https?://[^\s'\")]+)"),
    re.compile(r"(?:ba|z)?sh\s+-c\s+[\"']\$\(\s*(?:curl|wget)\b[^\n)]*?(https?://[^\s'\")]+)"),
]

R3_PATTERNS = [
    ("ssh",     re.compile(r"[~/\"'`]\.ssh(?:[/\"'`]|\b)|id_rsa\b|id_ed25519\b|authorized_keys\b")),
    ("aws",     re.compile(r"\.aws[/\\](?:credentials|config)\b|[\"'`/]\.aws[\"'`]")),
    ("gnupg",   re.compile(r"\.gnupg\b")),
    ("gcloud",  re.compile(r"application_default_credentials\.json|\.config[/\\]gcloud\b")),
    ("browser", re.compile(r"[\"'`/](?:Cookies|Login Data|Local State)[\"'`]|cookies\.sqlite|[\"'`/]logins\.json|key4\.db")),
    ("dotenv",  re.compile(r"\bload_dotenv\s*\(|require\(\s*['\"]dotenv['\"]\s*\)|from\s+['\"]dotenv['\"]|"
                           r"dotenv\.config\s*\(|readFileSync\([^)\n]*['\"`]\.env['\"`]|open\([^)\n]*['\"]\.env['\"]")),
    ("envkey",  re.compile(r"(?:process\.env|os\.environ|os\.getenv|env::var|os\.Getenv|\$env:)\W{0,3}\(?['\"]?"
                           r"[A-Z0-9_]*(?:TOKEN|SECRET|API_KEY|APIKEY|PASSWORD|PASSWD|PRIVATE_KEY)[A-Z0-9_]*")),
]
R3_BASE = {"ssh": "medium", "aws": "medium", "gnupg": "medium", "gcloud": "medium",
           "browser": "medium", "dotenv": "medium", "envkey": "low"}
R3_LABEL = {"ssh": "SSH 키 경로", "aws": "AWS 자격 증명", "gnupg": "GPG 키링", "gcloud": "GCP 자격 증명",
            "browser": "브라우저 쿠키·로그인 DB", "dotenv": ".env 로드", "envkey": "토큰·키 환경변수"}
# 차단·제외 목록 안의 언급인지 (흔한 오탐) 판단하는 단서
DENYLIST_HINT = re.compile(r"\b(deny|block|ignore|exclude|skip|forbid|sensitive|secret_paths|protected|"
                           r"blacklist|denylist|never|redact|disallow)", re.I)

R5_PATTERNS = [
    ("rm-root-home", "high",   re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?[a-zA-Z]*\s+(?:--\s+)?(?:/(?:\s|$|\*)|~/?(?:\s|$|\*)|\"?\$\{?HOME\}?/?\"?(?:\s|$|\*))")),
    ("chmod-777",    "medium", re.compile(r"\bchmod\s+(?:-R\s+)?0?777\b")),
    ("sudo",         "medium", re.compile(r"(?:^|[;&|`(]\s*|\s)sudo\s+(?!-v\b)[a-z]")),
    ("shell-profile","medium", re.compile(r"(?:>>|appendFile\w*\(|write_text\(|open\(|Add-Content)[^\n]{0,80}(?:\.bashrc|\.zshrc|\.bash_profile|\.zprofile|[~/]\.profile|\$PROFILE)\b|"
                                          r"(?:\.bashrc|\.zshrc|\.bash_profile|\.zprofile|[~/]\.profile)\b[^\n]{0,40}(?:>>|appendFile|\"a\"|'a')")),
]
R5_LABEL = {"rm-root-home": "루트·홈 전체 삭제", "chmod-777": "chmod 777", "sudo": "sudo 사용",
            "shell-profile": "셸 프로필 수정"}

# R9: 에이전트 설정 경로 참조 + 같은 파일 안 쓰기 동작
WRITE_OP = re.compile(r"writeJson\w*\(|write_json\w*\(|writeConfig\w*\(|writeSettings\w*\(|saveSettings\w*\(|writeFileSync|writeFile\(|fs\.promises\.writeFile|appendFileSync|"
                      r"write_text\(|json\.dump\(|open\([^)\n]*['\"][wa]\+?['\"]|"
                      r"fs::write|File::create|OpenOptions|os\.WriteFile|ioutil\.WriteFile|"
                      r"Set-Content|Out-File|Add-Content|\bcat\s*>|\btee\b|>>?\s*[\"']?\$?\{?\w*(?:HOME|CLAUDE)")
R9_RULES = [
    ("perm-allow", "high",   re.compile(r"permissions[\"']?\s*[\]:.\[]|\.permissions\b|[\"']allow[\"']\s*[:\]]|permissions\.allow")),
    ("mcp-config", "medium", re.compile(r"\.claude\.json\b|mcpServers")),
    ("instr-file", "medium", re.compile(r"(?:\.claude[/\\'\"`,\s]{1,6})?\b(?:CLAUDE|AGENTS|GEMINI)\.md\b")),
    ("settings-hooks", "medium", re.compile(r"settings(?:\.local)?\.json")),
]
R9_LABEL = {"perm-allow": "자동 허용 권한(permissions.allow) 등록", "mcp-config": "MCP 서버 설정(~/.claude.json·mcpServers) 수정",
            "instr-file": "에이전트 지시 파일(CLAUDE.md 등) 쓰기", "settings-hooks": "에이전트 settings.json 수정(훅 등록 등)"}
CLAUDE_DIR = re.compile(r"\.claude\b|CLAUDE_CONFIG_DIR|claude_dir|claudeDir|CLAUDE_HOME", re.I)
GLOBAL_HINT = re.compile(r"homedir\(\)|os\.homedir|Path\.home\(\)|expanduser|\$HOME|\$\{HOME\}|~/\.claude|"
                         r"home_dir\(\)|dirs::home|UserHomeDir|USERPROFILE", re.I)
MARKER_HINT = re.compile(r"<!--\s*[\w-]+[-_ ](?:begin|start)\s*-->|BEGIN [A-Z-]+|# >>> ", re.I)
CONSENT_HINT = re.compile(r"\bconfirm\s*\(|inquirer|\bprompts?\s*\(|Read-Host|\binput\s*\(|dialoguer|Confirm::new|"
                          r"\.confirm\(|askYesNo|ask_yes_no", re.I)
COMMENT_LINE = re.compile(r"^\s*(?://|#(?!!)|\*|/\*|--\s|REM\b|::|<!--)")
EXEC_CALL = re.compile(r"\b(?:exec(?:Sync|File|FileSync)?|spawn(?:Sync)?|system|popen|subprocess|"
                       r"Command::new|os\.system|run\(|check_call|check_output|execa|shell\.exec|Start-Process)\b")
SHELL_EXT = {".sh", ".bash", ".zsh", ".ps1", ".psm1", ".cmd", ".bat", ""}


def test_cutoff(p: Path, lines):
    """Rust 파일의 #[cfg(test)] 이후는 테스트 코드로 본다"""
    if p.suffix == ".rs":
        for i, ln in enumerate(lines):
            if ln.strip().startswith("#[cfg(test)]"):
                return i + 1
    return None


PIPE_IN_STRING = re.compile(r"""['"`][^'"`]*\|\s*(?:sudo\s+)?(?:ba|z)?sh\b[^'"`]*['"`]|['"`][^'"`]*\|\s*(?:iex|Invoke-Expression)\b""", re.I)
EXEC_CALL_R1 = re.compile(r"\b(?:exec(?:Sync|File|FileSync)?|spawn(?:Sync)?|system|popen|subprocess\.\w+|"
                          r"Command::new|os\.system|run|check_call|check_output|execa|shell\.exec|Start-Process)\s*\(")
COMMENT_LINE_R1 = re.compile(r"^\s*(?://|#(?!!)|\*|/\*)")
SHELL_EXT_R1 = {".sh", ".bash", ".zsh", ".ps1", ".psm1", ".cmd", ".bat", ""}


def adjust_r1(url: str, owner: str):
    u = url.lower()
    host_path = re.sub(r"^https?://", "", u)
    host = host_path.split("/")[0]
    adj, sev = [], "high"
    if re.match(r"^\d+\.\d+\.\d+\.\d+$", host) or host in {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd"}:
        return "high", ["IP 직접 지정·단축 URL +1"], host
    owner_l = owner.lower()
    if (host in {"raw.githubusercontent.com", "github.com", "objects.githubusercontent.com"}
            and host_path.split("/")[1:2] == [owner_l]) or owner_l in host:
        sev, adj = "medium", ["저장소 소유자 도메인 -1"]
    elif any(host_path.startswith(o) for o in OFFICIAL_INSTALLERS):
        sev, adj = "medium", ["제3자 공식 설치기 -1"]
    elif "$" in url or "{" in url:
        adj = ["URL이 변수라 출처 확인 불가"]
    return sev, adj, host


def scan_repo(folder: str, repo: Path):
    meta = TOOLS[folder]
    owner = folder.split("_", 1)[0]
    signals = []
    hook_files, n_hook_cfgs = scan_hooks(repo, signals, folder)
    has_uninstall = False
    n_files = 0
    for p in iter_files(repo):
        rel = str(p.relative_to(repo))
        text = read_text(p)
        if text is None:
            continue
        n_files += 1
        if re.search(r"\buninstall\b", rel, re.I):
            has_uninstall = True
        ctx = context_of(rel, hook_files)
        is_code = p.suffix.lower() in CODE_EXT or p.name == "package.json"
        lines = text.splitlines()

        # --- R1 (README·설치 스크립트·문서·코드 전부. 테스트는 참고만)
        for i, ln in enumerate(lines, 1):
            for rx in R1_PATTERNS:
                m = rx.search(ln)
                if m:
                    sev, adj, host = adjust_r1(m.group(1), owner)
                    if sev == "high" and host == "raw.githubusercontent.com" and \
                            re.search(rf"\b{re.escape(owner)}/", text, re.I):
                        sev, adj = "medium", ["URL이 문자열 결합이나, 파일 안 저장소 이름이 소유자와 일치 -1"]
                    signals.append(dict(tool=folder, rule="R1", sub="pipe-to-shell", file=rel, line=i,
                                        context=ctx, base="high", severity=sev, adjust=adj,
                                        detail=f"원격 스크립트를 셸로 바로 실행 · {host}",
                                        snippet=ln.strip()[:160], counted=ctx not in {"test"}))
                    break
        # R1-b: 실행 함수 인자 안에서 조립한 "다운로드 | 셸" (URL이 변수·상수라 위 패턴이 놓치는 경우)
        if p.suffix.lower() in CODE_EXT and p.suffix.lower() not in SHELL_EXT_R1:
            r1_lines = {x["line"] for x in signals if x["rule"] == "R1" and x["file"] == rel}
            for i, ln in enumerate(lines, 1):
                if i in r1_lines or COMMENT_LINE_R1.match(ln):
                    continue
                if PIPE_IN_STRING.search(ln) and EXEC_CALL_R1.search(ln):
                    owner_hit = re.search(rf"githubusercontent\.com/{re.escape(owner)}/|github\.com/{re.escape(owner)}/",
                                          text, re.I)
                    if owner_hit:
                        sev, adj = "medium", ["URL이 변수, 같은 파일의 상수가 저장소 소유자 도메인 -1"]
                    else:
                        sev, adj = "high", ["URL이 변수라 출처 확인 불가"]
                    when = "업데이트" if re.search(r"upgrade|update|self-?update", rel, re.I) else "사용"
                    signals.append(dict(tool=folder, rule="R1", sub="exec-pipe", file=rel, line=i,
                                        context=ctx, base="high", severity=sev, adjust=adj,
                                        detail=f"실행 함수 안에서 원격 스크립트를 셸로 바로 실행 ({when} 시점)",
                                        snippet=ln.strip()[:160], counted=ctx not in {"test"}, when=when))
        # package.json 설치 시점 스크립트
        if p.name == "package.json":
            try:
                pkg = json.loads(text)
            except Exception:
                pkg = {}
            for k in ("preinstall", "install", "postinstall"):
                v = (pkg.get("scripts") or {}).get(k)
                if v:
                    signals.append(dict(tool=folder, rule="R1", sub="npm-lifecycle", file=rel, line=0,
                                        context=ctx, base="medium", severity="medium", adjust=[],
                                        detail=f"npm {k} 스크립트(설치 시 자동 실행)", snippet=f"{k}: {v[:140]}",
                                        counted=ctx not in {"test"}))

        if not is_code:
            # 문서·지시문은 R3/R5/R9 코드 규칙 대상이 아니다. 지시문 속 위험 명령은 R8-b 후보로만 남긴다.
            if ctx == "instruction":
                for i, ln in enumerate(lines, 1):
                    for sub, _sev, rx in R5_PATTERNS:
                        if sub in {"rm-root-home", "chmod-777"} and rx.search(ln):
                            signals.append(dict(tool=folder, rule="R8-b?", sub=sub, file=rel, line=i,
                                                context=ctx, base="-", severity="범위 외", adjust=[],
                                                detail=f"지시문 속 {R5_LABEL[sub]} (3단계 R8-b 후보)",
                                                snippet=ln.strip()[:160], counted=False))
            continue

        counted_ctx = ctx in {"hook", "install", "code"}
        cut = test_cutoff(p, lines)
        is_shell = p.suffix.lower() in SHELL_EXT

        def line_ctx(i, ln):
            """줄 단위 맥락: (context, counted, note)"""
            if cut and i >= cut:
                return "test", False, "Rust 테스트 모듈"
            if COMMENT_LINE.match(ln):
                return ctx, False, "주석"
            return ctx, counted_ctx, ""

        # --- R3
        for i, ln in enumerate(lines, 1):
            for kind, rx in R3_PATTERNS:
                if rx.search(ln):
                    sev = R3_BASE[kind]
                    adj = []
                    allowed = any(kind in R3_ALLOW.get(c, set()) for c in meta["cat"])
                    if kind != "envkey":
                        if allowed:
                            sev, adj = "low", ["목적 일치 -1"]
                        else:
                            sev, adj = "high", ["목적 불일치 +1"]
                        window = "\n".join(lines[max(0, i - 7):i + 1])
                        if DENYLIST_HINT.search(window):
                            sev = {"high": "medium", "medium": "low"}.get(sev, sev)
                            adj.append("차단·제외 목록 안의 언급으로 보임 -1")
                    if ctx == "hook" and sev != "low":
                        adj.append("훅 스크립트 안(자동 실행)")
                    lc, cnt, note = line_ctx(i, ln)
                    if note:
                        adj.append(f"{note} → 참고")
                    signals.append(dict(tool=folder, rule="R3", sub=kind, file=rel, line=i, context=lc,
                                        base=R3_BASE[kind], severity=sev, adjust=adj,
                                        detail=R3_LABEL[kind], snippet=ln.strip()[:160],
                                        counted=cnt))
                    break

        # --- R5
        for i, ln in enumerate(lines, 1):
            for sub, base, rx in R5_PATTERNS:
                if rx.search(ln):
                    sev, adj = base, []
                    if sub == "shell-profile" and re.search(r"PATH", "\n".join(lines[max(0, i - 3):i + 3])):
                        sev, adj = "low", ["PATH 추가 목적의 프로필 수정 -1"]
                    lc, cnt, note = line_ctx(i, ln)
                    if note:
                        adj.append(f"{note} → 참고")
                    elif not is_shell and not EXEC_CALL.search(ln):
                        cnt = False
                        adj.append("셸 실행 호출 없는 문자열(안내 메시지·패턴 데이터) → 참고")
                    signals.append(dict(tool=folder, rule="R5", sub=sub, file=rel, line=i, context=lc,
                                        base=base, severity=sev, adjust=adj, detail=R5_LABEL[sub],
                                        snippet=ln.strip()[:160], counted=cnt))
                    break

        # --- R9 (파일 단위: 에이전트 설정 경로 + 쓰기 동작이 함께 있어야 함)
        if CLAUDE_DIR.search(text) and WRITE_OP.search(text):
            is_global = bool(GLOBAL_HINT.search(text))
            has_marker = bool(MARKER_HINT.search(text))
            for sub, base, rx in R9_RULES:
                hit_line = 0
                if sub == "perm-allow":
                    # permissions 와 allow 가 함께 나오고, 추가 동작이 있는 줄을 우선
                    cands = [i for i, ln in enumerate(lines, 1)
                             if re.search(r"permissions(?!\s*\()", ln) and re.search(r"\ballow\b", ln)
                             and not COMMENT_LINE.match(ln) and not (cut and i >= cut)]
                    adds = [i for i in cands if re.search(r"push\(|append\(|insert\(|\.add\(|=\s*\[|extend\(", lines[i - 1])]
                    hit_line = (adds or cands or [0])[0]
                else:
                    PRINT_LIKE = re.compile(r"\b(?:println!|eprintln!|print\(|console\.\w+\(|echo\b|Write-Host|note\(|log\.\w+\()")
                    cands = [i for i, ln in enumerate(lines, 1)
                             if rx.search(ln) and not COMMENT_LINE.match(ln) and not (cut and i >= cut)]
                    real = [i for i in cands if not PRINT_LIKE.search(lines[i - 1])]
                    hit_line = (real or cands or [0])[0]
                if not hit_line:
                    continue
                if sub == "settings-hooks" and not re.search(r"[\"']hooks[\"']|\.hooks\b|hooks\[", text):
                    continue
                sev, adj = base, []
                if not is_global:
                    sev = {"high": "medium", "medium": "low"}[sev]
                    adj.append("프로젝트 범위 설정 -1")
                else:
                    adj.append("전역(홈) 설정")
                if sub == "instr-file" and has_marker:
                    sev = {"high": "medium", "medium": "low"}.get(sev, sev)
                    adj.append("구분 마커로 감싼 섹션 -1")
                # 사용자 고지·동의 보정(-1)은 정적 탐지가 불안정해 자동 적용하지 않고 사람 라벨에 맡긴다
                signals.append(dict(tool=folder, rule="R9", sub=sub, file=rel, line=hit_line, context=ctx,
                                    base=base, severity=sev, adjust=adj, detail=R9_LABEL[sub],
                                    snippet=lines[hit_line - 1].strip()[:160], counted=counted_ctx,
                                    subj=f"{sub}:{'global' if is_global else 'project'}"))

    # 되돌리는 명령이 있으면 R9 한 단계 더 낮춤 (도구 단위)
    if has_uninstall:
        for s in signals:
            if s["rule"] == "R9" and s["severity"] in {"high", "medium"}:
                s["severity"] = {"high": "medium", "medium": "low"}[s["severity"]]
                s["adjust"].append("제거(uninstall) 경로 있음 -1")
    return signals, dict(files=n_files, hook_cfgs=n_hook_cfgs, hook_files=len(hook_files),
                         uninstall=has_uninstall)


# ---------------------------------------------------------------------------
# 5. 종합 판정
# ---------------------------------------------------------------------------
def verdict(signals):
    counted = [s for s in signals if s["counted"]]
    if any(s["severity"] == "high" for s in counted):
        return "주의"
    if any(s["severity"] == "medium" for s in counted):
        return "보통"
    return "낮음"


def main():
    repos_dir, out_dir = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    all_signals, summary = [], []
    for folder in sorted(TOOLS, key=lambda f: TOOLS[f]["no"]):
        repo = repos_dir / folder
        if not repo.is_dir():
            continue
        sigs, stats = scan_repo(folder, repo)
        all_signals.extend(sigs)
        cnt = defaultdict(lambda: defaultdict(int))
        for s in sigs:
            if s["counted"]:
                cnt[s["rule"]][s["severity"]] += 1
        summary.append(dict(no=TOOLS[folder]["no"], tool=TOOLS[folder]["name"], verdict=verdict(sigs),
                            stats=stats, counts={r: dict(v) for r, v in cnt.items()},
                            out_of_scope=sum(1 for s in sigs if s["rule"] == "R8-b?"),
                            ref_only=sum(1 for s in sigs if not s["counted"] and s["rule"] != "R8-b?")))
    with open(out_dir / "signals.jsonl", "w", encoding="utf-8") as f:
        for s in all_signals:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    for row in summary:
        print(row["no"], row["tool"], row["verdict"], row["counts"], "범위외", row["out_of_scope"],
              "참고", row["ref_only"], row["stats"])


if __name__ == "__main__":
    main()
