#!/usr/bin/env python3
"""대표 판정 실측 테스트: 도구 조합별로 Claude Code를 따로 실행해서 실제 토큰 사용과 동작을 잰다.

- 조합: none(플러그인 없음) / sp(superpowers) / ecc / both
- 각 실행은 빈 폴더에서, 사용자 설정 파일 대신 --settings 로 enabledPlugins 만 지정한다.
- 기록: init(불러온 플러그인·스킬 수), 사용량(usage), 비용, 호출된 스킬, 훅 이벤트
사용법: python run_real_test.py <조합> <프롬프트파일> <결과이름> [모델] [최대턴]
"""
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "real_test")
os.makedirs(OUT, exist_ok=True)
CLAUDE = os.environ.get("CLAUDE_BIN", os.path.expanduser("~/.local/bin/claude.exe"))
CWD = os.environ.get("REALTEST_CWD", os.path.join(HERE, "_cwd"))
os.makedirs(CWD, exist_ok=True)

PLUGINS = {
    "none": {},
    "sp": {"superpowers@superpowers-dev": True},
    "ecc": {"ecc@ecc": True},
    "both": {"superpowers@superpowers-dev": True, "ecc@ecc": True},
}


def main():
    combo, pfile, name = sys.argv[1], sys.argv[2], sys.argv[3]
    model = sys.argv[4] if len(sys.argv) > 4 else "haiku"
    turns = sys.argv[5] if len(sys.argv) > 5 else "1"
    prompt = open(pfile, encoding="utf-8").read().strip()
    settings = json.dumps({"enabledPlugins": PLUGINS[combo]})
    cmd = [CLAUDE, "-p", prompt, "--setting-sources", "project", "--settings", settings,
           "--strict-mcp-config", "--no-session-persistence", "--output-format", "stream-json", "--verbose",
           "--include-hook-events", "--model", model, "--max-turns", turns, "--permission-mode", "bypassPermissions"]
    r = subprocess.run(cmd, cwd=CWD, capture_output=True, text=True, encoding="utf-8", timeout=900)
    raw = os.path.join(OUT, f"{name}_{combo}.jsonl")
    open(raw, "w", encoding="utf-8").write(r.stdout)
    init, result, skills_called, hooks = None, None, [], []
    for line in r.stdout.splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        t, st = e.get("type"), e.get("subtype")
        if t == "system" and st == "init":
            init = e
        elif t == "result":
            result = e
        elif t == "assistant":
            for c in (e.get("message") or {}).get("content", []):
                if c.get("type") == "tool_use" and c.get("name") == "Skill":
                    skills_called.append((c.get("input") or {}).get("skill"))
        elif t == "system" and "hook" in (st or ""):
            hooks.append({"subtype": st, "name": e.get("hook_name") or e.get("hook_event"), "event": e.get("hook_event")})
    summ = {"combo": combo, "name": name, "model": model, "returncode": r.returncode, "stderr": r.stderr[-300:]}
    if init:
        summ["plugins"] = [p.get("name") if isinstance(p, dict) else p for p in init.get("plugins", [])]
        summ["skills_count"] = len(init.get("skills", []))
        summ["tools_count"] = len(init.get("tools", []))
        summ["slash_commands_count"] = len(init.get("slash_commands", []))
        summ["agents_count"] = len(init.get("agents", []))
    if result:
        u = result.get("usage", {})
        summ["usage"] = {k: u.get(k) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")}
        summ["context_in_tokens"] = sum((u.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
        summ["cost_usd"] = result.get("total_cost_usd")
        summ["num_turns"] = result.get("num_turns")
        summ["duration_ms"] = result.get("duration_ms")
        summ["result_text"] = (result.get("result") or "")[:300]
    summ["skills_called"] = skills_called
    summ["hook_events"] = hooks[:60]
    json.dump(summ, open(os.path.join(OUT, f"{name}_{combo}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: summ.get(k) for k in ("combo", "plugins", "skills_count", "context_in_tokens", "usage", "cost_usd", "skills_called", "returncode")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
