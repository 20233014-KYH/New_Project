#!/usr/bin/env python3
"""R3b: R3와 같은 과제를 '실제 배포처럼' React로 빌드한 사이트로. HTML에는 빈 <div id="root">뿐이고,
화면은 압축된 144KB 자바스크립트(React 포함)가 그린다 → 페이지 코드를 받아 읽기가 훨씬 어려운 상황.
- 사이트: r3b_src (vite build, 정상 dist_orig + 고장 4개 dist_text/left/del/filter)
- 조건·채점은 R3와 같음(run_r3.py를 그대로 쓰고 사이트·포트·폴더만 바꿈)
사용법: python run_r3b.py run [키 ...] | score
"""
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor

import run_r3 as r3

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "r3b_src")
r3.OUT = os.path.join(HERE, "..", "results_r3b")
os.makedirs(r3.OUT, exist_ok=True)
r3.v1.OUT = r3.OUT
r3.CWDS = os.path.join(HERE, "_cwd_r3", "b")  # 위 폴더의 node_modules(@playwright/test)를 찾아 쓰도록 그 안에 둔다
os.makedirs(r3.CWDS, exist_ok=True)
r3.PORT_BASE, r3.GRADE_BASE = 8940, 9400
DIST = {None: "dist_orig", "추가(글자 잘림)": "dist_text", "완료 개수": "dist_left", "삭제(엉뚱한 항목)": "dist_del", "필터": "dist_filter"}


def make_site(dst, mutant=None):
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(os.path.join(SRC, DIST[mutant]), dst)


r3.make_site = make_site

if __name__ == "__main__":
    if sys.argv[1] == "score":
        r3.score()
    else:
        keys = sys.argv[2:] or [f"{c}_r{r}" for r in range(1, 4) for c in r3.CONDS]
        with ThreadPoolExecutor(max_workers=3) as ex:
            for msg in ex.map(r3.run_one, keys):
                print(msg, flush=True)
