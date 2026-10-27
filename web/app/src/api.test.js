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
    expect(rec.remove[0].save).toBe(9169)
  })

  it('조건 shell=powershell → rtk 더하기 카드에 PowerShell 주의 문구, "지금 환경에서는 효과가 없어요"', async () => {
    const rec = await getRecommend(['caveman'], { work: '', shell: 'powershell', logs: '' })
    const rtkCard = rec.add.find(a => a.tool === 'rtk')
    expect(rtkCard).toBeDefined()
    expect(rtkCard.verdict).toBe('지금 환경에서는 효과가 없어요')
    expect(rtkCard.warnings.length).toBeGreaterThan(0)
  })

  it('판정 없는 쌍은 no_info이고 화면 문구는 "확인된 정보 없음"', async () => {
    // caveman(카테고리2)와 graphify(카테고리3) - 판정 없는 쌍
    const pairs = await judgeBox(['caveman', 'graphify'])
    const noInfo = pairs.find(p => p.state === 'no_info')
    expect(noInfo).toBeDefined()
    expect(noInfo.label).toBe('확인된 정보 없음')
  })
})

describe('도구 목록', () => {
  it('카테고리 1 필터 시 category=1 도구만 반환', async () => {
    const tools = await getTools({ categoryId: 1 })
    expect(tools.every(t => t.category === 1)).toBe(true)
    expect(tools.length).toBeGreaterThan(0)
  })
})
