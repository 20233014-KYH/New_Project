import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { searchTools, getCategories, fmt } from '../api.js'
import AddButton from '../components/AddButton.jsx'

function getBox() {
  try { return JSON.parse(sessionStorage.getItem('inv-box') || '[]') } catch { return [] }
}
function saveBox(ids) {
  try { sessionStorage.setItem('inv-box', JSON.stringify(ids)) } catch {}
}

export default function FindPage() {
  const [searchParams] = useSearchParams()
  const q = searchParams.get('q') || ''
  const [results, setResults] = useState([])
  const [box, setBox] = useState(getBox)
  const [catName, setCatName] = useState({})
  const [total, setTotal] = useState(0)

  useEffect(() => {
    getCategories().then(cats => {
      const map = {}
      cats.forEach(c => { map[c.id] = c.name })
      setCatName(map)
    })
    searchTools('').then(all => setTotal(all.length))
  }, [])

  useEffect(() => {
    if (!q) { setResults([]); return }
    searchTools(q).then(setResults)
  }, [q])

  function toggleBox(id) {
    const next = box.includes(id) ? box.filter(x => x !== id) : [...box, id]
    setBox(next)
    saveBox(next)
  }

  return (
    <main>
      <div className="c">
        <h1 tabIndex={-1}>"{q}" 찾은 결과 {results.length}개</h1>
        <p className="lead">이름, 저장소, 영어 설명에서 찾았어요.</p>

        {results.length === 0
          ? <div className="empty">
              맞는 도구가 없어요. 지금은 측정한 {total}개 안에서만 찾아요.{' '}
              <Link to="/browse/1">분야별로 둘러보기</Link>
            </div>
          : <div className="list">
              {results.map(t => (
                <div key={t.id} className="item">
                  <div>
                    <Link className="i-name" to={`/tool/${t.id}`}>{t.name}</Link>
                    <div className="i-repo">{t.repo}</div>
                    <div className="i-desc">{t.desc_en}</div>
                  </div>
                  <div className="i-tok">
                    {t.tokens == null
                      ? <><span className="n">—</span><small>측정 안 함</small></>
                      : <><span className="n">+{fmt(t.tokens)}</span><small>처음 읽는 양</small></>
                    }
                  </div>
                  <div className="i-meta">
                    {catName[t.category] && <div>{catName[t.category]}</div>}
                    {t.stars != null && <div>별 {fmt(t.stars)}</div>}
                  </div>
                  <div className="i-add">
                    <AddButton id={t.id} box={box} onToggle={toggleBox} />
                  </div>
                </div>
              ))}
            </div>
        }
      </div>
    </main>
  )
}
