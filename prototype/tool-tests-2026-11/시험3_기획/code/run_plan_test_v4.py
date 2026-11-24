#!/usr/bin/env python3
"""시험 3 기획 분야 남은 도구(v4): v3 장치를 그대로 쓰고 조건·상황만 더한다.

- ECC: v3의 어려운 상황 4개(S2·S3·S5·S6)에 조건 하나로 더함 (12번)
- pm-skills: 새 상황 S7 제품 기획서(PRD) 쓰기 x 조건 4개(none·plan·pm 자연어·pm_cmd 명령 직접) (12번)
- 결과는 v3와 같은 results_v3/ 에 쌓고, 채점은 score_v3.py
사용법: python run_plan_test_v4.py ecc | prd
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import run_plan_test_v3 as v3

REPOS = v3.v1.REPOS


def plugin_dirs(repo):
    # marketplace.json에 적힌 플러그인 폴더 전부(측정 때와 같은 전체 설치 기준)
    root = os.path.join(REPOS, repo)
    d = json.load(open(os.path.join(root, ".claude-plugin", "marketplace.json"), encoding="utf-8"))
    return [os.path.normpath(os.path.join(root, p["source"])) for p in d.get("plugins", []) if isinstance(p.get("source"), str)]


v3.SITUATIONS["S7"] = dict(
    fixture=None,
    prompt="동아리 회원 관리 웹 서비스의 제품 기획서(PRD)를 써 줘. 아직 개발 계획은 필요 없어.",
    answer="대상은 우리 동아리 임원 5명과 회원 50명이고, 지금은 엑셀과 카톡으로 회비와 출석을 관리해. 더 묻지 말고 기획서를 마무리해 줘.",
)
v3.CONDITIONS["ecc"] = dict(plugins=plugin_dirs("affaan-m_ECC"))
v3.CONDITIONS["pm"] = dict(plugins=plugin_dirs("phuryn_pm-skills"))
v3.CONDITIONS["pm_cmd"] = dict(plugins=plugin_dirs("phuryn_pm-skills"), prefix="/pm-execution:write-prd ")

JOBS = {
    "ecc": [f"{s}_ecc_r{r}" for r in range(1, 4) for s in ("S2", "S3", "S5", "S6")],
    "prd": [f"S7_{c}_r{r}" for r in range(1, 4) for c in ("none", "plan", "pm", "pm_cmd")],
}

if __name__ == "__main__":
    if os.path.isdir(v3.SKILLS):
        sys.exit("시험용 설정 폴더에 gstack(skills/)이 남아 있어요. run_plan_test_v3.py uninstall 먼저")
    with ThreadPoolExecutor(max_workers=4) as ex:
        for msg in ex.map(v3.run_one, JOBS[sys.argv[1]]):
            print(msg, flush=True)
