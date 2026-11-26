// 로컬 모드: VITE_API_BASE 없으면 src/data/ 파일에서 읽고 와이어프레임 logic.js 규칙으로 계산
// 필드 매핑: entries.always_on_tokens_est → tokens, entries.auto.stars/pushed_at/license → stars/pushed_at/license
// 조건 값: big_logs(api-draft) = logs(wireframe), unknown = ""(잘 모르겠어요), env.shell = shell

import entriesRaw from './data/entries.json'
import compatRaw from './data/compat.json'
import testedRaw from './data/tested.json'
import descRaw from './data/desc_en.json'
import cardsRaw from './data/cards_ko.json'
import traitsRaw from './data/tool_traits.json'
import situationCsv from './data/situation_rules.csv?raw'
import priorityCsv from './data/situation_priority.csv?raw'
import goalsCsv from './data/situation_goals.csv?raw'

// 서버 모드: VITE_API_BASE=http://localhost:8080/api (server/app, Spring). 같은 데이터·같은 규칙이라 결과 모양이 같다.
const BASE = import.meta.env.VITE_API_BASE || ''

// entries.json → 와이어프레임 tools 형식으로 변환
function normalizeEntry(e) {
  return {
    id: e.id,
    name: e.name,
    repo: e.repo,
    category: e.category,
    desc_en: e.desc_en || descRaw.desc?.[e.id] || '',
    summary_ko: cardsRaw.cards?.[e.id]?.summary_ko || null,
    when_ko: cardsRaw.cards?.[e.id]?.when_ko || null,
    version: e.version || null,
    license: e.auto?.license || null,
    stars: e.auto?.stars || null,
    pushed_at: e.auto?.pushed_at ? e.auto.pushed_at.slice(0, 10) : null,
    tokens: e.always_on_tokens_est ?? null,
    scope: e.scope || null,
    token_note: e.token_note || null,
    checked_at: e.checked_at || null,
    latest_release: e.auto?.latest_release || null,
    refreshed_at: e.auto?.refreshed_at || null,
  }
}

// compat.json pairs → 와이어프레임 pairs 형식으로 변환
// 검수 상태(review_state)와 근거 종류(evidence[].type)는 다른 값이라 섞지 않는다
function normalizePair(p) {
  return {
    a: p.a,
    b: p.b,
    relation: p.relation,
    review_state: p.review_state || 'ai_estimate',
    reason: p.reason_ko || null,
    sources: [...new Set((p.evidence || []).map(e => e.source).filter(Boolean))],
    judged_at: p.judged_at || null,
    same_role: !!p.same_role,
  }
}

let _tools = null
let _pairs = null
let _tested = null

function getLocalData() {
  if (!_tools) {
    _tools = (entriesRaw.entries || []).map(normalizeEntry)
    _pairs = (compatRaw.pairs || []).map(normalizePair)
    _tested = testedRaw
  }
  return { tools: _tools, pairs: _pairs, tested: _tested }
}

// --- 로컬 판정·추천 로직 (logic.js 포팅) ---

const KO = { overlap: '겹침', situational: '상황따라', complement: '보완', none: '관계 없음' }
const RS = { tested: '직접 시험', human_review: '사람 검토', ai_estimate: 'AI 추정' }

function pairKey(a, b) { return [a, b].sort().join('|') }

// 겹침 기준(compat.json criteria): 빈 세션이 처음 읽는 양의 5%
const OVERLAP_MIN = compatRaw.criteria?.overlap_min_tokens ?? 0
const comma = n => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',')

// 도구함 안에서 서로 모두 '같은 일'(same_role)인 3개 이상 묶음(최대 클리크). 큰 묶음 먼저, 같으면 도구함 순서
function roleGroups(ids, pairMap) {
  const adj = id => ids.filter(o => o !== id && pairMap[pairKey(id, o)]?.same_role)
  const out = []
  const bk = (R, P, X) => {
    if (!P.length && !X.length) {
      if (R.length >= 3) out.push(ids.filter(i => R.includes(i)))
      return
    }
    for (const v of [...P]) {
      const n = adj(v)
      bk([...R, v], P.filter(x => n.includes(x)), X.filter(x => n.includes(x)))
      P = P.filter(x => x !== v)
      X = [...X, v]
    }
  }
  bk([], [...ids], [])
  const lex = (a, b) => {
    for (let i = 0; i < Math.min(a.length, b.length); i++) if (a[i] !== b[i]) return a[i] - b[i]
    return a.length - b.length
  }
  return out.sort((a, b) => b.length - a.length || lex(a.map(x => ids.indexOf(x)), b.map(x => ids.indexOf(x))))
}

function buildIndex(tools, pairs) {
  const byId = Object.fromEntries(tools.map(t => [t.id, t]))
  const pairMap = Object.fromEntries(pairs.map(p => [pairKey(p.a, p.b), p]))
  const testedMap = Object.fromEntries((getLocalData().tested || []).map(t => [t.tool, t]))
  return { byId, pairMap, testedMap }
}

function judgeLocal(ids, byId, pairMap) {
  const out = []
  for (let i = 0; i < ids.length; i++) {
    for (let j = i + 1; j < ids.length; j++) {
      const p = pairMap[pairKey(ids[i], ids[j])]
      out.push(p
        ? { a: p.a, b: p.b, state: 'saved', relation: p.relation, label: KO[p.relation], review: RS[p.review_state],
            reason: p.reason, sources: p.sources, judged_at: p.judged_at }
        : { a: ids[i], b: ids[j], state: 'no_info', label: '확인된 정보 없음',
            review: byId[ids[i]]?.category === byId[ids[j]]?.category ? '판정 없음' : '다른 분야' })
    }
  }
  return out
}

function recommendLocal(ids, answers, byId, pairMap, testedMap) {
  const js = judgeLocal(ids, byId, pairMap)
  const remove = []
  js.filter(p => p.relation === 'overlap').forEach(p => {
    const a = byId[p.a], b = byId[p.b]
    if (!a || !b) return
    const big = (a.tokens || 0) >= (b.tokens || 0) ? a : b
    const keep = big === a ? b : a
    if (!remove.find(r => r.tool === big.id))
      remove.push({ tool: big.id, keep: keep.id, save: big.tokens || 0, review: p.review,
        reason: p.reason, sources: p.sources, judged_at: p.judged_at, group: null })
  })
  // 같은 일 묶음(3개 이상): 가장 큰 것을 남겨도 아끼는 양(합 - 최댓값)이 기준 이상이면 하나만 남긴다.
  // 남길 도구 = 아직 안 뺀 것 중 처음 읽는 양이 가장 작은 것(같으면 도구함 앞쪽) — 빼기 규칙과 같은 임시 규칙
  const tok = id => byId[id]?.tokens || 0
  roleGroups(ids, pairMap).forEach(g => {
    const saving = g.reduce((s, id) => s + tok(id), 0) - Math.max(...g.map(tok))
    if (saving < OVERLAP_MIN) return
    const free = g.filter(id => !remove.find(r => r.tool === id))
    if (free.length < 2) return
    const keep = free.reduce((k, id) => (tok(id) < tok(k) ? id : k))
    const names = g.map(id => byId[id]?.name || id).join(', ')
    free.filter(id => id !== keep).forEach(id => {
      const p = pairMap[pairKey(id, keep)]
      remove.push({ tool: id, keep, save: tok(id), review: RS[p.review_state],
        reason: `같은 일을 하는 도구 ${g.length}개(${names})를 함께 켰어요. 가장 큰 것을 남겨도 ${comma(saving)}토큰을 아껴서(기준 ${comma(OVERLAP_MIN)}토큰) 하나만 남기기를 권해요.`,
        sources: p.sources, judged_at: p.judged_at, group: g })
    })
  })
  const add = []
  Object.values(testedMap).forEach(t => {
    if (ids.includes(t.tool)) return
    const checks = ids.map(id => ({ id, p: pairMap[pairKey(id, t.tool)] }))
    const unknown = checks.filter(c => !c.p).map(c => c.id)
    const blocked = checks.find(c => c.p && c.p.relation === 'overlap')
    const warnings = []
    if (t.caution_work && answers.work === t.caution_work) warnings.push(t.caution)
    if (t.caution_shell && answers.shell === t.caution_shell) warnings.push(t.caution)
    const notFit = t.caution_shell && answers.shell === t.caution_shell
    add.push({
      tool: t.tool, effect: t.effect, caution: t.caution, warnings, unknown,
      blocked: blocked ? blocked.id : null,
      verdict: blocked ? '겹침이 있어 추천하지 않아요' : notFit ? '지금 환경에서는 효과가 없어요' : '조건을 확인하고 더해 보세요',
      date: t.date,
    })
  })
  return { pairs: js, remove, add, unknownCount: js.filter(p => p.state === 'no_info').length,
    situation: situationCard(answers?.situation, answers?.priority, ids, byId, pairMap),
    goal: goalPlan(answers || {}, ids, byId, pairMap, testedMap) }
}

// 서버 모드에서 서버가 꺼져 있거나 오류면 화면 위에 안내 띠를 띄운다(components/ServerBanner.jsx가 이 이벤트를 받음)
async function apiFetch(url, opts) {
  try {
    const res = await fetch(url, opts)
    if (!res.ok && res.status >= 500) throw new Error(`서버 오류 ${res.status}`)
    window.dispatchEvent(new CustomEvent('inv-server', { detail: { ok: true } }))
    return res
  } catch (e) {
    window.dispatchEvent(new CustomEvent('inv-server', { detail: { ok: false, url } }))
    throw e
  }
}

// --- API 함수 6개 (api-draft.md 2장) ---

// 1. 카테고리 목록
export async function getCategories() {
  if (BASE) {
    const res = await apiFetch(`${BASE}/categories`)
    return res.json()
  }
  // 로컬: data.js와 같은 카테고리 목록
  return [
    { id: 1, name: '기획·작업 방식', desc: 'Claude가 일하는 순서와 계획을 정해 줘요', when: 'Claude가 매번 제멋대로 일해서 순서와 규칙을 잡고 싶을 때' },
    { id: 2, name: '토큰·컨텍스트', desc: '토큰을 아끼고 맥락을 이어 줘요', when: '토큰이 너무 빨리 줄거나, 대화가 길어져 앞 내용을 잊을 때' },
    { id: 3, name: '코드 이해·검색', desc: '코드와 기술 문서를 찾고 이해하게 도와줘요', when: '큰 프로젝트에서 코드나 라이브러리 문서를 잘 찾게 하고 싶을 때' },
    { id: 4, name: '디자인·프론트엔드', desc: '화면을 만들고 다듬어 줘요', when: '화면을 만들거나 디자인 품질을 높이고 싶을 때' },
    { id: 5, name: '백엔드·인프라', desc: '서버·DB·클라우드 작업을 도와줘요', when: 'DB나 서버, 클라우드 작업을 Claude에게 시키고 싶을 때' },
    { id: 6, name: 'QA·테스트', desc: '테스트·리뷰·보안을 점검해 줘요', when: '테스트와 코드 리뷰, 보안 점검을 빠뜨리지 않고 싶을 때' },
  ]
}

// 2. 도구 목록 (카테고리 필터, 검색어)
export async function getTools({ categoryId, q } = {}) {
  if (BASE) {
    const params = new URLSearchParams()
    if (categoryId) params.set('category', categoryId)
    if (q) params.set('q', q)
    const res = await apiFetch(`${BASE}/tools?${params}`)
    return res.json()
  }
  const { tools } = getLocalData()
  let list = tools
  if (categoryId) list = list.filter(t => t.category === Number(categoryId))
  if (q) {
    const lq = q.toLowerCase()
    list = list.filter(t => t.name.toLowerCase().includes(lq) || (t.desc_en || '').toLowerCase().includes(lq) ||
      (t.summary_ko || '').toLowerCase().includes(lq))
  }
  return list
}

// 3. 도구 상세
export async function getTool(id) {
  if (BASE) {
    const res = await apiFetch(`${BASE}/tools/${id}`)
    return res.json()
  }
  const { tools, pairs } = getLocalData()
  const tool = tools.find(t => t.id === id)
  if (!tool) return null
  const relatedPairs = pairs.filter(p => p.a === id || p.b === id).map(p => ({
    ...p,
    otherId: p.a === id ? p.b : p.a,
    label: KO[p.relation],
    review: RS[p.review_state],
  }))
  return { ...tool, pairs: relatedPairs, situations: toolSituations(id, tools), traits: traitsRaw.traits?.[id] || null }
}

// 4. 도구함 쌍 판정 (저장된 판정만, no_info 포함)
export async function judgeBox(ids) {
  if (BASE) {
    const res = await apiFetch(`${BASE}/judge`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ids }) })
    return res.json()
  }
  const { tools, pairs } = getLocalData()
  const { byId, pairMap } = buildIndex(tools, pairs)
  return judgeLocal(ids, byId, pairMap)
}

// 5. 추천 (조건 포함)
// answers: { work: 'bugfix'|'feature'|'unknown', shell: 'bash'|'powershell'|'unknown', logs: 'big_logs'|'small'|'unknown' }
export async function getRecommend(ids, answers) {
  if (BASE) {
    const res = await apiFetch(`${BASE}/recommend`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ids, answers }) })
    return res.json()
  }
  const { tools, pairs } = getLocalData()
  const { byId, pairMap, testedMap } = buildIndex(tools, pairs)
  return recommendLocal(ids, answers, byId, pairMap, testedMap)
}

// 6. 도구 검색 (홈 검색)
// --- 상황별 추천 규칙 (data/situation_rules.csv = 용현 규칙 v1, 서버와 같은 파일) ---
// 결과 종류: 추가(깔면 더 좋아요) / 기본충분(시험해 보니 기본 기능으로 충분) / 주의(같은 상황 카드에 붙는 주의).
// 화면에서 빼는 줄: 근거가 제작자 설명(doc)뿐이거나 표시 수준에 '화면에 안 올림'이 있는 줄(팀 원칙 11-08, 블라인드 비교 대기)
export const hiddenRule = r => r.evidenceType === 'doc' || (r.display || '').includes('화면에 안 올림')
function splitCsv(line) {
  const out = []; let cur = ''; let q = false
  for (let i = 0; i < line.length; i++) {
    const ch = line[i]
    if (q) {
      if (ch === '"' && line[i + 1] === '"') { cur += '"'; i++ }
      else if (ch === '"') q = false
      else cur += ch
    } else if (ch === '"') q = true
    else if (ch === ',') { out.push(cur); cur = '' }
    else cur += ch
  }
  out.push(cur)
  return out
}
let _rules = null
function getRules() {
  if (!_rules) {
    const lines = situationCsv.replace(/\uFEFF/g, '').split(/\r?\n/).filter(l => l.trim())
    _rules = lines.slice(1).map(l => {
      const c = splitCsv(l)
      return { ruleId: c[0], category: Number(c[1]), id: c[2], label: c[3], base: c[4], tools: c[5], better: c[6],
        cost: c[7], evidenceType: c[8], source: c[9], review: c[10], resultType: c[11] || '추가', display: c[13] || '' }
    }).filter(r => !hiddenRule(r))
  }
  return _rules
}
// 상황마다 대표 줄 하나(주의 줄 제외)
const mainRules = () => getRules().filter(r => r.resultType !== '주의')
// 상황 + 중요한 것 → 고를 도구 (data/situation_priority.csv, 서버와 같은 파일). 시험에서 차이가 확인된 조합만 있다
export const PRIORITY_LABEL = { accurate: '틀리지 않는 것', quality: '결과 품질', save: '토큰·한도 아끼기', simple: '설치·관리가 간단한 것', safe: '실수로 망가뜨리지 않는 것', fast: '빨리 끝내기' }
const PRIORITY_ORDER = ['accurate', 'quality', 'save', 'fast', 'simple', 'safe']
let _picks = null
function getPicks() {
  if (!_picks) {
    const lines = priorityCsv.replace(/\uFEFF/g, '').split(/\r?\n/).filter(l => l.trim())
    _picks = Object.fromEntries(lines.slice(1).map(l => {
      const c = splitCsv(l)
      return [`${c[0]}|${c[1]}`, { tools: c[2], reason: c[3] }]
    }))
  }
  return _picks
}
function toolRef(t, ids, byId, pairMap) {
  return { id: t, name: byId[t]?.name || t, inBox: ids.includes(t),
    overlapWith: clashWith(t, ids, pairMap, 'overlap'), similarTo: clashWith(t, ids, pairMap, 'situational') }
}
// 안 골랐거나 시험에서 차이를 확인 못 한 조합이면 null. base = 기본 기능으로 충분
function pick(situationId, priority, ids, byId, pairMap) {
  if (!priority) return null
  const p = getPicks()[`${situationId}|${priority}`]
  if (!p) return null
  const base = p.tools === 'base'
  return { priority, label: PRIORITY_LABEL[priority], base,
    tools: base ? [] : p.tools.split('|').map(t => t.trim()).filter(Boolean).map(t => toolRef(t, ids, byId, pairMap)),
    reason: p.reason }
}
// 추천 도구가 도구함의 도구와 겹침(overlap)·상황따라(situational) 판정이면 그 도구 id를 모은다. 이미 담은 도구는 빈 목록
function clashWith(t, ids, pairMap, relation) {
  if (ids.includes(t)) return []
  return ids.filter(id => pairMap[pairKey(id, t)]?.relation === relation)
}
// 도구 상세: 이 도구가 추천 도구로 들어간 상황(규칙 파일 순서)과 그 상황의 중요한 것별 고르기
const splitTools = s => s.split('|').map(t => t.trim()).filter(Boolean)
function toolSituations(id, tools) {
  const names = Object.fromEntries(tools.map(t => [t.id, t.name]))
  const picks = getPicks()
  return getRules().filter(r => splitTools(r.tools).includes(id)).map(r => ({
    id: r.id, label: r.label, base: r.base, better: r.better, cost: r.cost, resultType: r.resultType,
    evidence: r.evidenceType === 'tested' ? '직접 시험' : '제작자 설명',
    picks: PRIORITY_ORDER.filter(pr => picks[`${r.id}|${pr}`]).map(pr => {
      const p = picks[`${r.id}|${pr}`]
      return { priority: pr, label: PRIORITY_LABEL[pr],
        chosen: p.tools === 'base' ? '기본 기능' : splitTools(p.tools).map(t => names[t] || t).join(' 또는 '), reason: p.reason }
    }),
  }))
}
// 고른 상황의 3칸 카드: 기본 기능으로도 / 이럴 땐 깔면 더 좋아요 / 대신. 안 골랐거나 없는 상황이면 null
function situationCard(situationId, priority, ids, byId, pairMap) {
  if (!situationId) return null
  const r = mainRules().find(x => x.id === situationId)
  if (!r) return null
  const refs = s => s.split('|').map(t => t.trim()).filter(Boolean).map(t => toolRef(t, ids, byId, pairMap))
  return {
    resultType: r.resultType, display: r.display,
    cautions: getRules().filter(x => x.id === r.id && x.resultType === '주의').map(x => ({ tools: refs(x.tools), text: x.better, cost: x.cost })),
    id: r.id, category: r.category, label: r.label, base: r.base,
    tools: r.tools.split('|').map(t => t.trim()).filter(Boolean).map(t => toolRef(t, ids, byId, pairMap)),
    better: r.better, cost: r.cost, evidence: r.evidenceType === 'tested' ? '직접 시험' : '제작자 설명',
    source: r.source, review: r.review, pick: pick(r.id, priority, ids, byId, pairMap),
  }
}

// 목적 → 상황 여러 개 (data/situation_goals.csv, 서버와 같은 파일)
let _goals = null
function getGoalRows() {
  if (!_goals) {
    const lines = goalsCsv.replace(/\uFEFF/g, '').split(/\r?\n/).filter(l => l.trim())
    _goals = lines.slice(1).map(l => { const c = splitCsv(l); return { id: c[0], label: c[1], desc: c[2], situations: c[3] } })
  }
  return _goals
}
export async function getGoals() {
  if (BASE) {
    const res = await apiFetch(`${BASE}/goals`)
    return res.json()
  }
  return getGoalRows().map(g => ({ id: g.id, label: g.label, desc: g.desc }))
}
// 같은 도구가 여러 상황에서 나오면 한 줄로 합친다
function mergePlan(m, t, situation, reason, warnings) {
  const old = m.get(t.id)
  if (!old) { m.set(t.id, { tool: t.id, name: t.name, situations: [situation], reasons: [reason], warnings: [...warnings] }); return }
  old.situations.push(situation)
  old.reasons.push(reason)
  warnings.forEach(w => { if (!old.warnings.includes(w)) old.warnings.push(w) })
}
// 목적 → 더하기 / 꺼도 되는 것 / 그대로 + 상황별 카드 (서버 JudgeService.goalPlan과 같은 규칙)
function goalPlan(ans, ids, byId, pairMap, testedMap) {
  if (!ans.goal) return null
  const g = getGoalRows().find(x => x.id === ans.goal)
  if (!g) return null
  const cards = splitTools(g.situations).map(s => situationCard(s, ans.priority, ids, byId, pairMap)).filter(Boolean)
  const add = new Map(), off = new Map(), keep = new Map()
  const costMatters = ['save', 'fast', 'simple'].includes(ans.priority)
  for (const c of cards) {
    const p = c.pick
    if (!p) continue
    if (p.base) {
      if (costMatters) c.tools.filter(t => t.inBox).forEach(t => mergePlan(off, t, c.label, p.reason, []))
      continue
    }
    // '또는'으로 묶인 도구는 하나만: 도구함에 이미 있는 쪽을 그대로, 없으면 첫 번째만 더하기 (서버 JudgeService.goalPlan과 같음)
    const inBoxPick = p.tools.filter(t => t.inBox)
    for (const t of (inBoxPick.length ? inBoxPick : p.tools.slice(0, 1))) {
      if (t.inBox) { mergePlan(keep, t, c.label, p.reason, []); continue }
      const warnings = [...t.overlapWith.map(o => `도구함의 ${o}와 겹쳐요`), ...t.similarTo.map(o => `도구함의 ${o}와 비슷한 역할이에요(상황따라)`)]
      const tt = testedMap[t.id]
      if (tt && ((tt.caution_work && tt.caution_work === ans.work) || (tt.caution_shell && tt.caution_shell === ans.shell))) warnings.push(tt.caution)
      mergePlan(add, t, c.label, p.reason, warnings)
    }
  }
  return { id: g.id, label: g.label, desc: g.desc, add: [...add.values()], turnOff: [...off.values()], keep: [...keep.values()], situations: cards }
}

// 상황 질문의 선택지
export async function getSituations() {
  if (BASE) {
    const res = await apiFetch(`${BASE}/situations`)
    return res.json()
  }
  return mainRules().map(r => ({ id: r.id, category: r.category, label: r.label }))
}

export async function searchTools(q) {
  return getTools({ q })
}

// 유틸: 카테고리 이름 찾기
export async function getCategoryName(id) {
  const cats = await getCategories()
  return cats.find(c => c.id === Number(id))?.name || ''
}

// 숫자 포맷 (한국어 천 단위)
export const fmt = n => n != null ? new Intl.NumberFormat('ko-KR').format(n) : '—'
