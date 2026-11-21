#!/usr/bin/env python3
"""R1b: 진짜 큰 코드(gradio, 파이썬 파일 772개)에서 "같은 원인 더 찾기". trailofbits가 자기 스킬을 평가할 때 쓰는 과제를 그대로 씀.

- 코드: gradio @45c11d52 + trailofbits의 gradio-vulns.patch (work/gradio, git 기록은 지움 → diff로 답을 볼 수 없음)
- 알려 주는 것: processing_utils.py의 extract_video_thumbnail 명령 주입(씨앗)
- 정답: flagging.py의 archive_flagged_media (os.system, 다른 함수·다른 모듈 → 씨앗과 같은 함수 이름으로 찾으면 못 찾음)
- 함정: screen_recording_utils.py의 probe_recording_duration (안전함) — 취약하다고 적으면 헛경보
- 조건: nat / tob 설치만 / tob_named 스킬 이름 부름. 읽기 전용(쓰기·명령 실행 막음), 셋이 같은 폴더를 읽기만 함.
사용법: python run_r1b.py run [키 ...] | score
"""
import glob
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import run_r1 as r1  # 깨끗한 환경·최대 턴 80·trailofbits 경로를 그대로 씀

v1 = r1.v1
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results_r1b")
GRADIO = os.path.normpath(os.path.join(HERE, "..", "work", "gradio"))
os.makedirs(OUT, exist_ok=True)
v1.OUT = OUT
v1.ALLOWED = "Read,Glob,Grep,Skill,TodoWrite,Task"
v1.DENIED = "Write,Edit,Bash,PowerShell,WebFetch,WebSearch"

PROMPT = ("gradio/processing_utils.py:1110의 extract_video_thumbnail()에서 명령 주입 취약점을 찾았어. 업로드된 영상 경로와 "
          "호출자가 준 timestamp를 ffmpeg 명령 문자열에 넣고 subprocess.run(..., shell=True)로 실행해서, 파일 이름에 셸 특수문자가 "
          "있으면 임의 명령이 실행돼. 이 저장소에 같은 원인의 문제가 또 있는지 찾아 줘. 코드는 고치지 마. "
          "마지막에 '취약 목록:' 줄 아래에 찾은 곳을 한 줄에 하나씩 `파일경로:함수이름` 형식으로 적어 줘(씨앗 포함). "
          "그다음 '비슷하지만 안전:' 줄 아래에 검토했지만 안전하다고 본 곳을 같은 형식으로 적어 줘.")
CONDITIONS = {
    "nat": dict(prompt=PROMPT),
    "tob": dict(prompt=PROMPT, plugins=r1.TOB),
    "tob_named": dict(prompt="trailofbits의 variant-analysis 스킬을 써서 해 줘. " + PROMPT, plugins=r1.TOB),
}
TARGET, DECOY, SEED = "archive_flagged_media", "probe_recording_duration", "extract_video_thumbnail"


def run_one(key):
    cname, rep = key.rsplit("_r", 1)
    out = os.path.join(OUT, f"{key}.json")
    if os.path.exists(out):
        return f"{key}: 이미 있음"
    cond = CONDITIONS[cname]
    t = v1.run_turn(GRADIO, cond, cond["prompt"], key, 1)
    u = v1.tokens(t["usage"])
    rec = dict(condition=cname, rep=int(rep), turn=t, tokens=dict(total_in=u["input"] + u["cache_create"] + u["cache_read"], output=u["output"]))
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return f"{key}: 끝 ({t['sec']}초, rc={t['rc']}, 스킬={t['skills']})"


def section(text, head, stop=None):
    i = text.rfind(head)
    if i < 0:
        return None
    body = text[i + len(head):]
    if stop and stop in body:
        body = body[:body.index(stop)]
    return body


def score():
    for cname in CONDITIONS:
        print(f"\n[{cname}]")
        for f in sorted(glob.glob(os.path.join(OUT, f"{cname}_r?.json"))):
            r = json.load(open(f, encoding="utf-8"))
            t = r["turn"]
            text = t.get("result") or "\n".join(t["texts"])
            vuln = section(text, "취약 목록", "비슷하지만 안전") or ""
            safe = section(text, "비슷하지만 안전") or ""
            names = set(re.findall(r"\.py\s*[:：]\s*(?:\w+\.)?(\w+)", vuln))
            extra = sorted(names - {TARGET, SEED})
            print(f"  정답 찾음 {int(TARGET in names)}/1  함정(안전)을 취약이라 함 {int(DECOY in names)}  함정을 안전이라 함 {int(DECOY in safe)}  "
                  f"그 밖에 취약이라 한 곳 {len(extra)}개 {extra[:6]}  토큰 {r['tokens']['total_in'] + r['tokens']['output']:,}  "
                  f"시간 {t['sec']}초  스킬 {t['skills']}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
    else:
        keys = sys.argv[2:] or [f"{c}_r{r}" for r in range(1, 4) for c in CONDITIONS]
        with ThreadPoolExecutor(max_workers=3) as ex:
            for msg in ex.map(run_one, keys):
                print(msg, flush=True)
