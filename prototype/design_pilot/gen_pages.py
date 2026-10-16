#!/usr/bin/env python3
"""디자인 판정 파일럿 1단계: 같은 과제를 '도구 없음 / 도구 설명서 적용' 조건으로 생성한다.

- 생성 모델은 무료 라우터의 gpt-oss-120b 하나로 고정한다(조건 사이에 모델이 달라지지 않게).
- '도구 적용' = 그 도구의 설명서(SKILL.md 등)를 시스템 지시문으로 주는 것. 실제 Claude Code 플러그인
  실행과는 다르다(스크립트·훅·대화형 단계가 없음). 이 파일럿은 '측정 방법이 쓸 만한가'를 보는 것이 목적이다.
- 출력: pages/<과제>_<조건>_<회차>.html
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(HERE, "pages")
os.makedirs(PAGES, exist_ok=True)

KEY = os.environ["FREELLM_API_KEY"]  # 키는 환경변수로만 받는다(저장소에 넣지 않음)
URL = os.environ.get("FREELLM_URL", "http://127.0.0.1:3101/v1/chat/completions")
MODEL = "gpt-oss-120b"
HOME = os.path.expanduser("~")

FD = open(os.path.join(HOME, ".claude", "skills", "frontend-design", "SKILL.md"), encoding="utf-8").read()
IMP_DIR = os.path.join(HOME, ".claude", "plugins", "cache", "impeccable", "impeccable", "4.0.4", "skills", "impeccable")
IMP = open(os.path.join(IMP_DIR, "SKILL.md"), encoding="utf-8").read() + "\n\n" + \
      open(os.path.join(IMP_DIR, "reference", "craft-floor.md"), encoding="utf-8").read()

CONDITIONS = {
    "none": None,
    "fd": FD,    # frontend-design 설명서
    "imp": IMP,  # impeccable 설명서 + craft-floor
}
TASKS = {
    "login": "A login screen for a small team-planning web app called 'Plango'. Email, password, 'remember me', a primary sign-in button, a 'forgot password' link, and a way to create an account. Include an error state for a wrong password.",
    "dash": "An admin dashboard page for an online bookstore: a top bar with search and user menu, a left navigation, three summary figures (today's orders, revenue, returns), a table of the 6 most recent orders with status labels, and an empty-state for a 'low stock alerts' list.",
}
COMMON = (
    "Write ONE self-contained HTML file (inline CSS and JS only; no external fonts, CDNs, images or libraries). "
    "You have no shell or file access in this environment: do any design planning silently, and reply with only the final HTML inside a single ```html code block. "
    "It must work at 375px and 1280px widths."
)


def call(system, user, temperature):
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": user})
    body = json.dumps({"model": MODEL, "messages": msgs, "temperature": temperature, "max_tokens": 12000}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


def extract(text):
    m = re.search(r"```html\s*(.*?)```", text, re.S)
    if m:
        return m.group(1).strip()
    m = re.search(r"(<!DOCTYPE html.*</html>)", text, re.S | re.I)
    return m.group(1).strip() if m else None


def main():
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    log = []
    for task, tdesc in TASKS.items():
        for cond, sysmsg in CONDITIONS.items():
            for n in range(1, reps + 1):
                out = os.path.join(PAGES, f"{task}_{cond}_{n}.html")
                if os.path.exists(out):
                    continue
                prompt = f"Design and build: {tdesc}\n\n{COMMON}"
                html = None
                for attempt in range(4):
                    try:
                        text = call(sysmsg, prompt, 0.7)
                        html = extract(text)
                        if html:
                            break
                        print("   HTML 추출 실패, 재시도")
                    except Exception as e:
                        print("   오류:", str(e)[:120])
                        time.sleep(20 * (attempt + 1))
                if html:
                    open(out, "w", encoding="utf-8").write(html)
                    print(f"저장 {os.path.basename(out)} ({len(html)}자)", flush=True)
                    log.append({"file": os.path.basename(out), "chars": len(html)})
                else:
                    print(f"실패 {task}_{cond}_{n}", flush=True)
                time.sleep(6)
    json.dump(log, open(os.path.join(HERE, "gen_log.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
