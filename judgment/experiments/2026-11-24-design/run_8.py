"""시험 8: 디자인 분야(④) — 도구 없음 / impeccable / taste-skill / ui-ux-pro-max
- D1 다듬기(정답 있음): 결함 10개를 심은 설정 화면을 "더 좋게 다듬어 줘" → grade.js가 고친 개수를 셈. 2번씩.
- D3 새 랜딩 페이지(블라인드): "작은 커피 로스터리 랜딩 페이지" → 흔한 AI 모양 지표 + 사람이 가리고 비교. 1번씩
  (taste-skill은 제작자가 한 번에 30~45분·토큰 수십만이라고 밝혀서 횟수를 줄임).
- 시킬 말에 도구 이름을 넣지 않음(자연어로 부탁했을 때 도구가 알아서 쓰이는지까지 보려고). 실제로 부른 스킬은 기록.
- 깨끗한 설정(CLAUDE_CONFIG_DIR=~/.claude-clean), 모델 sonnet, 도구는 --plugin-dir로 이 실행에만 불러옴(설치 안 함).
- 결과는 실행마다 저장해서 끊겨도 이어서 함.
사용: python run_8.py
"""
import json, os, shutil, subprocess, sys, time

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
RUNS = os.path.join(HERE, "_runs")
CLAUDE = os.path.expanduser("~/.local/bin/claude.exe")
CLEAN = os.path.expanduser("~/.claude-clean")
REPOS = os.path.join(HERE, "..", "prototype", "pilot_judgment", "measure36", "repos")
NM = os.environ.get("NM") or os.path.join(HERE, "node_modules")
COND = {
    "none": [],
    "impeccable": [os.path.expanduser("~/.claude/plugins/cache/impeccable/impeccable/4.0.4")],
    "taste": [os.path.normpath(os.path.join(REPOS, "Leonxlnx_taste-skill"))],
    "uiux": [os.path.normpath(os.path.join(REPOS, "nextlevelbuilder_ui-ux-pro-max-skill"))],
}
# 이름을 불러 시키는 조건: 자연어 부탁만으로는 taste-skill·ui-ux-pro-max가 한 번도 불리지 않아서(D1 1차) 추가
CALL = {
    "taste_call": ("taste", {"d1": "taste-skill의 redesign-skill 스킬을 써서 ", "d3": "taste-skill의 taste-skill 스킬을 써서 "}),
    "uiux_call": ("uiux", {"d1": "ui-ux-pro-max 스킬을 써서 ", "d3": "ui-ux-pro-max 스킬을 써서 "}),
}
PLAN = [("d1", c, 2) for c in ["none", "impeccable", "taste", "uiux", "taste_call", "uiux_call"]] +        [("d3", c, 1) for c in ["none", "impeccable", "taste_call", "uiux_call"]]
TASKS = {
    "d1": ("이 폴더의 index.html 화면을 더 좋게 다듬어 줘. 내용과 기능은 그대로 두고, 결과도 index.html 한 파일로 남겨 줘.", 2),
    "d3": ("작은 커피 로스터리의 랜딩 페이지를 만들어 줘. 이 폴더에 index.html 한 파일로 만들어 줘. 사진 파일은 없어도 돼요.", 1),
}
os.makedirs(OUT, exist_ok=True)
os.makedirs(RUNS, exist_ok=True)


def run_one(task, cond, rep):
    name = f"{task}_{cond}_r{rep}"
    dst = os.path.join(OUT, name + ".json")
    if os.path.exists(dst):
        return json.load(open(dst, encoding="utf-8"))
    cwd = os.path.join(RUNS, name)
    if os.path.exists(cwd):
        shutil.rmtree(cwd)
    if task == "d1":
        shutil.copytree(os.path.join(HERE, "fixture_d1"), cwd)
    else:
        os.makedirs(cwd)
    prompt, _ = TASKS[task]
    plug = cond
    if cond in CALL:
        plug, pre = CALL[cond]
        prompt = pre[task] + prompt
    cmd = [CLAUDE, "-p", prompt, "--setting-sources", "project", "--settings", "{}", "--strict-mcp-config",
           "--no-session-persistence", "--output-format", "stream-json", "--verbose", "--model", "sonnet",
           "--max-turns", "80", "--permission-mode", "bypassPermissions"]
    for p in COND[plug]:
        cmd += ["--plugin-dir", p]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=cwd, env=dict(os.environ, CLAUDE_CONFIG_DIR=CLEAN), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=3000)
        stdout, rc, err = r.stdout, r.returncode, r.stderr
    except subprocess.TimeoutExpired as ex:
        stdout = ex.stdout if isinstance(ex.stdout, str) else (ex.stdout or b"").decode("utf-8", "replace")
        rc, err = -1, "timeout"
    open(os.path.join(OUT, name + ".jsonl"), "w", encoding="utf-8").write(stdout)
    skills, usage, plugins, turns, result = [], {}, None, None, ""
    for line in stdout.splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("type") == "system" and e.get("subtype") == "init":
            plugins = [p.get("name") if isinstance(p, dict) else p for p in e.get("plugins", [])]
        elif e.get("type") == "assistant":
            for c in (e.get("message") or {}).get("content", []):
                if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Skill":
                    skills.append((c.get("input") or {}).get("skill") or (c.get("input") or {}).get("command"))
        elif e.get("type") == "result":
            usage, turns, result = e.get("usage") or {}, e.get("num_turns"), e.get("result") or ""
    if "hit your" in result:
        sys.exit(f"사용 한도에 걸려 멈춤: {name}")
    html = os.path.join(cwd, "index.html")
    grade = {}
    if os.path.exists(html):
        g = subprocess.run(["node", os.path.join(HERE, "grade.js"), task, html, os.path.join(OUT, name + "_grade.json"),
                            os.path.join(OUT, name + ".png")], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=dict(os.environ, NM=NM))
        try:
            grade = json.load(open(os.path.join(OUT, name + "_grade.json"), encoding="utf-8"))
        except Exception:
            grade = {"error": g.stderr[-300:]}
    u = {k: usage.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")}
    res = {"task": task, "cond": cond, "rep": rep, "sec": round(time.time() - t0), "rc": rc, "plugins": plugins, "skills": skills,
           "turns": turns, "has_html": os.path.exists(html), "grade": grade, "usage": u, "total_tokens": sum(u.values()),
           "price_weighted": round(u["input_tokens"] + 1.25 * u["cache_creation_input_tokens"] + 0.1 * u["cache_read_input_tokens"] + 5 * u["output_tokens"]),
           "stderr_tail": (err or "")[-300:]}
    json.dump(res, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return res


if __name__ == "__main__":
    for task, cond, reps in PLAN:
        for rep in range(1, reps + 1):
            if True:
                x = run_one(task, cond, rep)
                g = x["grade"]
                score = f"{g.get('score')}/10 내용{'O' if g.get('contentOk') else 'X'}" if task == "d1" else f"AI모양 {g.get('aiLook')}/4"
                print(f"{task}_{cond}_r{rep}: {score}  스킬 {x['skills']}  토큰 {x['total_tokens']:,} (가중 {x['price_weighted']:,})  {x['sec']}초",
                      flush=True)
