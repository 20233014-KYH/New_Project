#!/usr/bin/env python3
"""시험 3 v3 블라인드 비교 자료 만들기.

상황마다 1회차(r1) 계획 5개를 도구 이름이 드러나는 줄을 지우고 A~E로 섞어 한 HTML에 담는다.
팀원은 어느 도구 결과인지 모른 채 계획을 고르고, 정답표(blind_key.json)는 고른 뒤에 연다.
사용법: python make_blind.py [시드]
"""
import html
import json
import os
import random
import re
import sys

from score_v2 import written

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results_v3")
OUT = os.path.join(HERE, "..", "블라인드")
CONDS = ["none", "plan", "sp", "gstack", "gstack_cmd"]
TITLES = {"S2": "큰 새 프로젝트", "S3": "목적이 흐릿한 새 아이디어", "S5": "욕심 많은 요구", "S6": "꼬인 기존 코드에 기능 추가"}
# 도구 이름이나 실행 방식이 드러나는 줄은 통째로 지운다
LEAK = re.compile(r"superpowers|gstack|office.?hours|brainstorm|writing-plans|계획 모드|플랜 모드|plan mode|ExitPlanMode|"
                  r"\.claude|plans[\\/]|스킬|skill|프리앰블|preamble|qid|AskUserQuestion|승인 요청|NotebookLM|"
                  r"^\s*[-*]?\s*(Branch|Status|모드|상태)\s*:|Builder|빌더|Implementation Plan|\*\*Goal:\*\*|^#\s*Design:", re.I)
# 도구마다 굳어진 머리말(## Context 등)은 줄만 남기지 않고 제목을 바꾼다
RENAME = [(re.compile(r"^##\s*Context\s*$", re.M), "## 배경")]


def final_plan(key):
    r = json.load(open(os.path.join(RES, f"{key}.json"), encoding="utf-8"))
    said = "\n\n".join((r["turn2"] or {}).get("texts", []) or r["turn1"]["texts"])
    # 계획을 파일로 남기는 조건은 대화엔 요약만 있어서, 대화가 짧으면 파일에 쓴 계획 중 가장 긴 것을 쓴다
    files = [written(os.path.join(RES, f"{key}_t{n}.jsonl")) for n in (2, 1)]
    text = said if len(said) >= 1500 else max([said] + files, key=len)
    for pat, rep in RENAME:
        text = pat.sub(rep, text)
    lines = [ln for ln in text.splitlines() if not LEAK.search(ln)]
    return r["prompt"], "\n".join(lines).strip()


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 20261113
    rng = random.Random(seed)
    os.makedirs(OUT, exist_ok=True)
    key, parts = {}, []
    import run_plan_test_v3 as v3
    for s, title in TITLES.items():
        order = CONDS[:]
        rng.shuffle(order)
        key[s] = {chr(65 + i): c for i, c in enumerate(order)}
        prompt = re.sub(r"^/office-hours ", "", v3.SITUATIONS[s]["prompt"])
        cards = []
        for i, c in enumerate(order):
            _, plan = final_plan(f"{s}_{c}_r1")
            cards.append(f'<section class="plan"><h3>계획 {chr(65 + i)}</h3><div class="md" data-md="{html.escape(plan, quote=True)}"></div></section>')
        parts.append(f'<article><h2>{s} {title}</h2><p class="req"><b>요청</b> {html.escape(prompt)}</p>'
                     f'<p class="req"><b>추가로 알려 준 것</b> {html.escape(v3.SITUATIONS[s]["answer"])}</p>{"".join(cards)}</article>')
    json.dump({"seed": seed, "key": key}, open(os.path.join(OUT, "blind_key.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    page = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>기획 블라인드 비교</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"></script>
<style>
:root{{--bg:#fafaf7;--fg:#1d1f21;--mute:#6b6f73;--card:#fff;--line:#e3e1da;--accent:#0f766e}}
@media (prefers-color-scheme:dark){{:root{{--bg:#16181a;--fg:#e8e6e1;--mute:#9a9ea3;--card:#1f2224;--line:#33373a;--accent:#5eead4}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.65 system-ui,"Malgun Gothic",sans-serif}}
main{{max-width:980px;margin:0 auto;padding:24px 16px 80px}}
h1{{font-size:26px;margin:0 0 8px}} h2{{margin:48px 0 8px;font-size:22px;border-bottom:2px solid var(--accent);padding-bottom:6px}}
.how{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 20px}}
.req{{color:var(--mute);margin:4px 0}}
.plan{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 20px 16px;margin:16px 0}}
.plan h3{{color:var(--accent);margin:12px 0 4px}}
.md{{overflow-wrap:anywhere}} .md table{{border-collapse:collapse;display:block;overflow-x:auto}} .md td,.md th{{border:1px solid var(--line);padding:4px 8px}}
.md pre{{white-space:pre-wrap}}
</style></head><body><main>
<h1>기획 블라인드 비교</h1>
<div class="how"><p><b>하는 법 (상황마다 2~3분)</b></p>
<ol><li>상황마다 계획 A~E를 읽어요. 어느 도구로 만든 건지는 가려 두었어요.</li>
<li>"내가 이 상황이면 어떤 계획대로 하고 싶은가"를 기준으로 <b>가장 좋은 것 1개</b>와 <b>가장 아쉬운 것 1개</b>를 골라요.</li>
<li>고른 이유를 한 줄씩 적어요. 길이가 길다고 좋은 건 아니에요.</li>
<li>다 고른 뒤에 노형원에게 보내요. 정답(어느 도구인지)은 모두 고른 뒤에 공개해요.</li></ol>
<p>적는 양식: <code>S2 좋음 _ / 아쉬움 _ / 이유: …</code></p></div>
{"".join(parts)}
</main><script>
document.querySelectorAll('.md').forEach(function(el){{var t=el.getAttribute('data-md');
try{{el.innerHTML=marked.parse(t)}}catch(e){{var p=document.createElement('pre');p.textContent=t;el.appendChild(p)}}}});
</script></body></html>"""
    path = os.path.join(OUT, "기획_블라인드_비교.html")
    open(path, "w", encoding="utf-8").write(page)
    print("만듦:", path)


if __name__ == "__main__":
    main()
