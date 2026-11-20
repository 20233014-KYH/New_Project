// 서버(Spring)가 로컬 모드와 같은 답을 주는지 확인한다.
// 서버를 켠 뒤: SERVER_URL=http://localhost:8080/api npm test   (SERVER_URL이 없으면 건너뜀)
import { describe, it, expect } from 'vitest'
import * as local from './api.js'

const SERVER = process.env.SERVER_URL

// null과 '값 없음'은 화면에서 똑같이 보이므로 같은 것으로 본다
const strip = v => JSON.parse(JSON.stringify(v, (k, x) => (x === null ? undefined : x)))
const get = async p => (await fetch(SERVER + p)).json()
const post = async (p, body) =>
  (await fetch(SERVER + p, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })).json()

const ANSWERS = [
  { work: '', shell: '', logs: '' },
  { work: 'bugfix', shell: 'powershell', logs: '' },
  { work: 'feature', shell: 'bash', logs: 'big_logs' },
  { work: '', shell: '', logs: '', situation: 'site-debug' },
  { work: 'bugfix', shell: 'bash', logs: '', situation: 'e2e-test' },
  { work: '', shell: '', logs: '', situation: 'security' },
  { work: '', shell: '', logs: '', situation: 'code-find' },
  { work: '', shell: '', logs: '', situation: 'multi-day' },
  { work: '', shell: '', logs: '', situation: 'big-tool-output', priority: 'accurate' },
  { work: '', shell: '', logs: '', situation: 'db-ask', priority: 'safe' },
  { work: '', shell: '', logs: '', situation: 'code-find', priority: 'save' },
  { work: '', shell: '', logs: '', situation: 'usage-view', priority: 'simple' },
  { work: '', shell: '', logs: '', situation: 'no-such-situation' },
]

describe.skipIf(!SERVER)('서버 = 로컬 모드', () => {
  it('분야 6개', async () => {
    expect(strip(await get('/categories'))).toEqual(strip(await local.getCategories()))
  })

  it('상황 질문 선택지(situation_rules.csv)', async () => {
    expect(strip(await get('/situations'))).toEqual(strip(await local.getSituations()))
  })

  it('도구 목록 36개(분야 필터·검색 포함)', async () => {
    expect(strip(await get('/tools'))).toEqual(strip(await local.getTools()))
    for (const c of [1, 2, 3, 4, 5, 6]) expect(strip(await get(`/tools?category=${c}`))).toEqual(strip(await local.getTools({ categoryId: c })))
    for (const q of ['graph', '원시인', 'mcp']) expect(strip(await get(`/tools?q=${encodeURIComponent(q)}`))).toEqual(strip(await local.getTools({ q })))
  })

  it('도구 상세 36개 전부', async () => {
    for (const t of await local.getTools()) expect(strip(await get(`/tools/${t.id}`))).toEqual(strip(await local.getTool(t.id)))
  })

  it('도구함 판정·추천: 분야별 묶음 + 36개 전부(630쌍) × 답 13가지(상황·중요한 것·겹침 경고 포함)', async () => {
    const all = (await local.getTools()).map(t => t.id)
    const boxes = [['superpowers', 'ecc', 'caveman'], ['caveman', 'graphify'], ['serena', 'gsd-core'], all]
    for (const c of [1, 2, 3, 4, 5, 6]) boxes.push((await local.getTools({ categoryId: c })).map(t => t.id))
    for (const ids of boxes) {
      expect(strip(await post('/judge', { ids }))).toEqual(strip(await local.judgeBox(ids)))
      for (const answers of ANSWERS) expect(strip(await post('/recommend', { ids, answers }))).toEqual(strip(await local.getRecommend(ids, answers)))
    }
  })
})
