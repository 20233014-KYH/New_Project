#!/usr/bin/env python3
"""대표 판정 1건(superpowers x ECC) 1단계: 두 도구의 스킬을 실제 파일에서 읽어 겹치는 기능을 찾는다.

- 입력: 내 PC에 설치된 두 플러그인의 skills/*/SKILL.md (frontmatter의 name, description)
- 방법: 이름 정규화 일치 + 설명 단어 유사도(TF-IDF 코사인). 사람이 상위 후보를 읽어 확정한다.
- 출력: skills_*.json, overlap_candidates.json
"""
import glob
import json
import math
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.expanduser("~/.claude/plugins/cache")
SP = os.path.join(CACHE, "superpowers-dev", "superpowers", "6.2.0", "skills")
EC = os.path.join(CACHE, "ecc", "ecc", "2.2.0", "skills")


def read_skills(root):
    out = []
    for f in sorted(glob.glob(os.path.join(root, "*", "SKILL.md"))):
        txt = open(f, encoding="utf-8", errors="ignore").read()
        m = re.match(r"---\s*\n(.*?)\n---", txt, re.S)
        fm = m.group(1) if m else ""
        name = re.search(r"^name:\s*(.+)$", fm, re.M)
        desc = re.search(r"^description:\s*(.+?)(?=\n[a-z_-]+:|\Z)", fm, re.M | re.S)
        folder = os.path.basename(os.path.dirname(f))
        out.append({
            "folder": folder,
            "name": (name.group(1).strip().strip("\"'") if name else folder),
            "description": re.sub(r"\s+", " ", desc.group(1)).strip().strip("\"'>|- ") if desc else "",
            "chars": len(txt),
        })
    return out


sp, ec = read_skills(SP), read_skills(EC)
json.dump(sp, open(os.path.join(HERE, "skills_superpowers.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(ec, open(os.path.join(HERE, "skills_ecc.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"superpowers 스킬 {len(sp)}개, ECC 스킬 {len(ec)}개")

STOP = set("the a an and or of to for in on with your you that this it is are be as by from at into any all can use using more not has have one its their via per than when use before after skill skills".split())
tok = lambda s: [w for w in re.findall(r"[a-z][a-z0-9]{2,}", s.lower()) if w not in STOP]
docs = {("sp", s["folder"]): tok(s["folder"].replace("-", " ") + " " + s["description"]) for s in sp}
docs.update({("ec", s["folder"]): tok(s["folder"].replace("-", " ") + " " + s["description"]) for s in ec})
N = len(docs)
df = Counter(w for t in docs.values() for w in set(t))


def vec(t):
    c = Counter(t)
    v = {w: (1 + math.log(n)) * math.log((N + 1) / (df[w] + 1)) for w, n in c.items()}
    nrm = math.sqrt(sum(x * x for x in v.values())) or 1
    return {w: x / nrm for w, x in v.items()}


V = {k: vec(t) for k, t in docs.items()}
cos = lambda a, b: sum(x * b.get(w, 0) for w, x in a.items())
ecd = {s["folder"]: s for s in ec}

# 이름이 거의 같은 스킬
norm = lambda s: re.sub(r"[^a-z]", "", s.lower())
print("\n[이름이 비슷한 스킬]")
for s in sp:
    for e in ec:
        a, b = norm(s["folder"]), norm(e["folder"])
        if a == b or a in b or b in a:
            print(f"  {s['folder']}  ~  {e['folder']}")

print("\n[superpowers 스킬별 ECC 쪽 가장 비슷한 스킬 상위 3]")
result = []
for s in sp:
    scores = sorted(((cos(V[("sp", s["folder"])], V[("ec", e["folder"])]), e["folder"]) for e in ec), reverse=True)[:3]
    result.append({"superpowers": s["folder"], "sp_description": s["description"], "matches": [{"ecc": n, "score": round(sc, 2), "ecc_description": ecd[n]["description"]} for sc, n in scores]})
    print(f"  {s['folder']:<34} " + " | ".join(f"{n}({sc:.2f})" for sc, n in scores))
json.dump(result, open(os.path.join(HERE, "overlap_candidates.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
