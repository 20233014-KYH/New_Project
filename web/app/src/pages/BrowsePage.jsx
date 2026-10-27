import { useState, useEffect } from 'react'
import { Link, NavLink, useParams } from 'react-router-dom'
import { getCategories, getTools, judgeBox, fmt } from '../api.js'
import AddButton from '../components/AddButton.jsx'

function getBox() {
  try { return JSON.parse(sessionStorage.getItem('inv-box') || '[]') } catch { return [] }
}
function saveBox(ids) {
  try { sessionStorage.setItem('inv-box', JSON.stringify(ids)) } catch {}
}

export default function BrowsePage() {
  const { categoryId } = useParams()
  const catId = Number(categoryId) || 1
  const [categories, setCategories] = useState([])
  const [tools, setTools] = useState([])
  const [q, setQ] = useState('')
  const [sort, setSort] = useState('stars')
  const [box, setBox] = useState(getBox)
  const [clashMap, setClashMap] = useState({})

  useEffect(() => { getCategories().then(setCategories) }, [])

  useEffect(() => {
    getTools({ categoryId: catId }).then(setTools)
    setQ('')
  }, [catId])

  useEffect(() => {
    if (!box.length) { setClashMap({}); return }
    judgeBox(box).then(pairs => {
      const map = {}
      pairs.filter(p => p.relation === 'overlap').forEach(p => {
        map[p.a] = (map[p.a] || []).concat(p.b)
        map[p.b] = (map[p.b] || []).concat(p.a)
      })
      setClashMap(map)
    })
  }, [box])

  function toggleBox(id) {
    const next = box.includes(id) ? box.filter(x => x !== id) : [...box, id]
    setBox(next)
    saveBox(next)
  }

  const cat = categories.find(c => c.id === catId)
  const filtered = tools
    .filter(t => !q.trim() || t.name.toLowerCase().includes(q.toLowerCase()) || (t.desc_en || '').toLowerCase().includes(q.toLowerCase()))
    .sort((a, b) => sort === 'tokens' ? (a.tokens ?? 1e9) - (b.tokens ?? 1e9) : (b.stars || 0) - (a.stars || 0))

  return (
    <main>
      <div className="c">
        <nav style={{ marginBottom: 'var(--s8)' }}>
          <div className="choice" role="navigation" aria-label="분야">
            {categories.map(c => (
              <NavLink
                key={c.id}
                className="opt"
                to={`/browse/${c.id}`}
                aria-current={c.id === catId ? 'page' : undefined}
              >
                {c.name}
              </NavLink>
            ))}
          </div>
        </nav>

        <h1 tabIndex={-1}>{cat?.name || ''}</h1>
        {cat && <p className="lead">{cat.desc}. 이럴 때 찾으세요: {cat.when}</p>}

        <div className="toolbar">
          <label htmlFor="bq">이 분야에서 찾기</label>
          <input
            id="bq"
            type="search"
            value={q}
            onChange={e => setQ(e.target.value)}
            autoComplete="off"
          />
          <label htmlFor="bs">정렬</label>
          <select id="bs" value={sort} onChange={e => setSort(e.target.value)}>
            <option value="stars">별 많은 순</option>
            <option value="tokens">처음 읽는 양 적은 순</option>
          </select>
          <span className="count n" aria-live="polite">{filtered.length}개</span>
        </div>

        <div className="list">
          {filtered.length === 0
            ? <div className="empty" style={{ marginTop: 'var(--s4)' }}>이 분야에서 "{q}"와 맞는 도구가 없어요.</div>
            : filtered.map(t => (
              <div key={t.id} className="item">
                <div>
                  <Link className="i-name" to={`/tool/${t.id}`}>{t.name}</Link>
                  <div className="i-repo">{t.repo}</div>
                  <div className="i-desc">{t.desc_en}</div>
                  {clashMap[t.id] && box.includes(t.id) && (
                    <div className="clash">도구함의 {clashMap[t.id].join(', ')}와 겹쳐요</div>
                  )}
                </div>
                <div className="i-tok">
                  {t.tokens == null
                    ? <><span className="n">—</span><small>측정 안 함</small></>
                    : <><span className="n">+{fmt(t.tokens)}</span><small>처음 읽는 양</small>
                        <div className="i-bar" style={{ width: `${Math.min(100, (t.tokens / 10000) * 100)}%` }} /></>
                  }
                </div>
                <div className="i-meta">
                  {t.stars != null && <div>별 {fmt(t.stars)}</div>}
                  {t.pushed_at && <div>{t.pushed_at.slice(0, 10)}</div>}
                </div>
                <div className="i-add">
                  <AddButton id={t.id} box={box} onToggle={toggleBox} />
                </div>
              </div>
            ))
          }
        </div>
      </div>
    </main>
  )
}
