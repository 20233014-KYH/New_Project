// 로컬 모드: VITE_API_BASE 없으면 src/data/ 파일에서 읽고 와이어프레임 logic.js 규칙으로 계산
// 필드 매핑: entries.always_on_tokens_est → tokens, entries.auto.stars/pushed_at/license → stars/pushed_at/license
// 조건 값: big_logs(api-draft) = logs(wireframe), unknown = ""(잘 모르겠어요), env.shell = shell

import entriesRaw from './data/entries.json'
import compatRaw from './data/compat.json'
import testedRaw from './data/tested.json'

const BASE = import.meta.env.VITE_API_BASE || ''

// entries.json → 와이어프레임 tools 형식으로 변환
function normalizeEntry(e) {
  return {
    id: e.id,
    name: e.name,
    repo: e.repo,
    category: e.category,
    desc_en: e.desc_en || '',
    version: e.version || null,
    license: e.auto?.license || null,
    stars: e.auto?.stars || null,
    pushed_at: e.auto?.pushed_at ? e.auto.pushed_at.slice(0, 10) : null,
    tokens: e.always_on_tokens_est ?? null,
    scope: e.scope || null,
    token_note: e.token_note || null,
    checked_at: e.checked_at || null,
  }
}

// compat.json pairs → 와이어프레임 pairs 형식으로 변환
function normalizePair(p) {
  return {
    a: p.a,
    b: p.b,
    relation: p.relation,
    review_state: p.evidence?.[0]?.type || 'human_review',
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
        ? { a: p.a, b: p.b, state: 'saved', relation: p.relation, label: KO[p.relation], review: RS[p.review_state] }
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
      remove.push({ tool: big.id, keep: keep.id, save: big.tokens || 0, review: p.review })
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
  return { pairs: js, remove, add, unknownCount: js.filter(p => p.state === 'no_info').length }
}

// --- API 함수 6개 (api-draft.md 2장) ---

// 1. 카테고리 목록
export async function getCategories() {
  if (BASE) {
    const res = await fetch(`${BASE}/categories`)
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
    const res = await fetch(`${BASE}/tools?${params}`)
    return res.json()
  }
  const { tools } = getLocalData()
  let list = tools
  if (categoryId) list = list.filter(t => t.category === Number(categoryId))
  if (q) {
    const lq = q.toLowerCase()
    list = list.filter(t => t.name.toLowerCase().includes(lq) || (t.desc_en || '').toLowerCase().includes(lq))
  }
  return list
}

// 3. 도구 상세
export async function getTool(id) {
  if (BASE) {
    const res = await fetch(`${BASE}/tools/${id}`)
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
  return { ...tool, pairs: relatedPairs }
}

// 4. 도구함 쌍 판정 (저장된 판정만, no_info 포함)
export async function judgeBox(ids) {
  if (BASE) {
    const res = await fetch(`${BASE}/judge`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ids }) })
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
    const res = await fetch(`${BASE}/recommend`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ids, answers }) })
    return res.json()
  }
  const { tools, pairs } = getLocalData()
  const { byId, pairMap, testedMap } = buildIndex(tools, pairs)
  return recommendLocal(ids, answers, byId, pairMap, testedMap)
}

// 6. 도구 검색 (홈 검색)
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
