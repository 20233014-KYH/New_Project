import { describe, it, expect } from 'vitest'
import { judgeBox, getRecommend, getTools } from './api.js'

describe('로컬 모드 판정', () => {
  it('[superpowers, ecc, caveman] → 겹침 1쌍(superpowers×ecc), 빼기 후보 ecc(처음 읽는 양 9,169)', async () => {
    const pairs = await judgeBox(['superpowers', 'ecc', 'caveman'])
    const overlaps = pairs.filter(p => p.relation === 'overlap')
    expect(overlaps).toHaveLength(1)
    expect(overlaps[0]).toMatchObject({ a: 'superpowers', b: 'ecc', relation: 'overlap' })

    const rec = await getRecommend(['superpowers', 'ecc', 'caveman'], { work: '', shell: '', logs: '' })
    expect(rec.remove).toHaveLength(1)
    expect(rec.remove[0].tool).toBe('ecc')
    expect(rec.remove[0].save).toBe(17491) // 2026-11-21 Claude Code 2.1.318로 다시 잰 값
    expect(rec.remove[0].group).toBeNull()
  })

  it('같은 일 묶음 3개: 둘씩은 상황따라여도 합쳐서 기준(1,642)을 넘으면 가장 작은 것만 남긴다', async () => {
    const box = ['graphify', 'codegraph', 'understand-anything'] // 795 · 1,109 · 1,355
    expect((await judgeBox(box)).filter(p => p.relation === 'overlap')).toHaveLength(0)
    const rec = await getRecommend(box, { work: '', shell: '', logs: '' })
    expect(rec.remove.map(r => r.tool)).toEqual(['codegraph', 'understand-anything'])
    expect(rec.remove.every(r => r.keep === 'graphify' && r.group.join() === box.join())).toBe(true)
    expect(rec.remove[0].reason).toContain('1,904')
    const two = await getRecommend(['graphify', 'codegraph'], { work: '', shell: '', logs: '' })
    expect(two.remove).toHaveLength(0)
  })

  it('조건 shell=powershell → rtk 더하기 카드에 PowerShell 주의 문구, "지금 환경에서는 효과가 없어요"', async () => {
    const rec = await getRecommend(['caveman'], { work: '', shell: 'powershell', logs: '' })
    const rtkCard = rec.add.find(a => a.tool === 'rtk')
    expect(rtkCard).toBeDefined()
    expect(rtkCard.verdict).toBe('지금 환경에서는 효과가 없어요')
    expect(rtkCard.warnings.length).toBeGreaterThan(0)
  })

  it('다른 분야 쌍도 AI 추정 판정이 있고, 카탈로그 36개끼리는 판정 없는 쌍이 없다', async () => {
    // 2026-11-21 다른 분야 540쌍을 Claude·Codex 교차 판정으로 채움
    const pairs = await judgeBox(['caveman', 'graphify'])
    expect(pairs[0].state).toBe('saved')
    expect(pairs[0].review).toBe('AI 추정')
    const all = (await getTools()).map(t => t.id)
    expect((await judgeBox(all)).filter(p => p.state === 'no_info')).toHaveLength(0)
  })
})

describe('도구 목록', () => {
  it('카테고리 1 필터 시 category=1 도구만 반환', async () => {
    const tools = await getTools({ categoryId: 1 })
    expect(tools.every(t => t.category === 1)).toBe(true)
    expect(tools.length).toBeGreaterThan(0)
  })
})

describe('판정 근거가 화면까지 전달됨', () => {
  it('검수 상태를 그대로 유지: 사람 검토 87쌍, 직접 시험 4쌍, AI 추정 539쌍', async () => {
    const { getTool } = await import('./api.js')
    const ids = (await getTools()).map(t => t.id)
    const seen = new Map()
    for (const id of ids) for (const p of (await getTool(id)).pairs) seen.set([p.a, p.b].sort().join('|'), p.review)
    const counts = [...seen.values()].reduce((m, r) => ({ ...m, [r]: (m[r] || 0) + 1 }), {})
    expect(counts['사람 검토']).toBe(87)
    expect(counts['직접 시험']).toBe(4)
    expect(counts['AI 추정']).toBe(539)
  })

  it('저장된 판정에는 이유·출처·확인일이 붙음', async () => {
    const [p] = await judgeBox(['superpowers', 'ecc'])
    expect(p.reason).toBeTruthy()
    expect(p.sources.length).toBeGreaterThan(0)
    expect(p.judged_at).toBe('2026-10-19')
    const rec = await getRecommend(['superpowers', 'ecc'], { work: '', shell: '' })
    expect(rec.remove[0].reason).toBeTruthy()
  })

  it('도구 설명(영어 원문)이 비어 있지 않음', async () => {
    const tools = await getTools()
    expect(tools.filter(t => !t.desc_en)).toHaveLength(0)
  })
})
