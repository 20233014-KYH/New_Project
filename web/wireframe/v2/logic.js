// 두 디자인(tastemaker, taste-skill)이 같이 쓰는 판정·추천 규칙. 화면 모양은 각 페이지가 정한다.
// 규칙 출처: 기획안 v2.1 6-5(쌍 판정 → 효율 근거 → 추천), server/api-draft.md
(() => {
  const D = window.INVENTORY;
  const byId = Object.fromEntries(D.tools.map(t => [t.id, t]));
  const key = (a, b) => [a, b].sort().join("|");
  const pairs = Object.fromEntries(D.pairs.map(p => [key(p.a, p.b), p]));
  const tested = Object.fromEntries((D.tested || []).map(t => [t.tool, t]));
  const KO = { overlap: "겹침", situational: "상황따라", complement: "보완", none: "관계 없음" };
  const RS = { tested: "직접 시험", human_review: "사람 검토", ai_estimate: "AI 추정" };
  const fmt = n => new Intl.NumberFormat("ko-KR").format(n);
  const clean = s => (s || "").replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE0F}]/gu, "").replace(/\s{2,}/g, " ").trim();
  const disp = t => (["skills", "mcp"].includes(t.name) ? t.repo.split("/")[0] : t.name);

  // 도구함 (이 탭 안에서만 유지)
  let box = [];
  try { box = JSON.parse(sessionStorage.getItem("inv-box") || "[]").filter(id => byId[id]); } catch (e) { box = []; }
  const save = () => { try { sessionStorage.setItem("inv-box", JSON.stringify(box)); } catch (e) { /* 저장 안 돼도 화면은 동작 */ } };
  const Box = {
    list: () => box.slice(),
    has: id => box.includes(id),
    toggle: id => { box = box.includes(id) ? box.filter(x => x !== id) : [...box, id]; save(); },
    clear: () => { box = []; save(); },
    sum: () => box.reduce((s, id) => s + (byId[id].tokens || 0), 0),
  };

  // 쌍 판정: saved / no_info (다른 분야이거나 판정 없음)
  function judge(ids) {
    const out = [];
    for (let i = 0; i < ids.length; i++) for (let j = i + 1; j < ids.length; j++) {
      const p = pairs[key(ids[i], ids[j])];
      out.push(p ? { a: p.a, b: p.b, state: "saved", relation: p.relation, label: KO[p.relation], review: RS[p.review_state] }
                 : { a: ids[i], b: ids[j], state: "no_info", label: "확인된 정보 없음", review: byId[ids[i]].category === byId[ids[j]].category ? "판정 없음" : "다른 분야" });
    }
    return out;
  }

  // 추천: 빼기(겹침 쌍에서 처음 읽는 양이 큰 쪽) / 더하기(직접 시험한 후보만, 조건 붙여서)
  function recommend(ids, answers) {
    const js = judge(ids);
    const remove = [];
    js.filter(p => p.relation === "overlap").forEach(p => {
      const a = byId[p.a], b = byId[p.b];
      const big = (a.tokens || 0) >= (b.tokens || 0) ? a : b, keep = big === a ? b : a;
      if (!remove.find(r => r.tool === big.id)) remove.push({ tool: big.id, keep: keep.id, save: big.tokens || 0, review: p.review });
    });
    const add = [];
    Object.values(tested).forEach(t => {
      if (ids.includes(t.tool)) return;
      const checks = ids.map(id => ({ id, p: pairs[key(id, t.tool)] }));
      const unknown = checks.filter(c => !c.p).map(c => c.id);
      const blocked = checks.find(c => c.p && c.p.relation === "overlap");
      const warnings = [];
      if (t.caution_work && answers.work === t.caution_work) warnings.push(t.caution);
      if (t.caution_shell && answers.shell === t.caution_shell) warnings.push(t.caution);
      const notFit = t.caution_shell && answers.shell === t.caution_shell;
      add.push({ tool: t.tool, effect: t.effect, caution: t.caution, warnings, unknown, blocked: blocked ? blocked.id : null,
                 verdict: blocked ? "겹침이 있어 추천하지 않아요" : notFit ? "지금 환경에서는 효과가 없어요" : "조건을 확인하고 더해 보세요", date: t.date });
    });
    return { pairs: js, remove, add, unknownCount: js.filter(p => p.state === "no_info").length };
  }

  window.INV = { D, byId, key, pairs, judge, recommend, Box, KO, RS, fmt, clean, disp,
    categories: D.categories, catOf: id => D.categories.find(c => c.id === id) };
})();
