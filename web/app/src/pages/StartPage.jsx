import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getCategories, getTools, fmt } from '../api.js'
import AddButton from '../components/AddButton.jsx'

function getBox() {
  try { return JSON.parse(sessionStorage.getItem('inv-box') || '[]') } catch { return [] }
}
function saveBox(ids) {
  try { sessionStorage.setItem('inv-box', JSON.stringify(ids)) } catch {}
}

export default function StartPage() {
  const [categories, setCategories] = useState([])
  const [picked, setPicked] = useState(null)
  const [starters, setStarters] = useState([])
  const [box, setBox] = useState(getBox)
  const navigate = useNavigate()

  useEffect(() => {
    getCategories().then(setCategories)
  }, [])

  useEffect(() => {
    if (!picked) { setStarters([]); return }
    getTools({ categoryId: picked }).then(tools => {
      const sorted = tools.filter(t => t.tokens != null).sort((a, b) => a.tokens - b.tokens).slice(0, 3)
      setStarters(sorted)
    })
  }, [picked])

  function toggleBox(id) {
    const next = box.includes(id) ? box.filter(x => x !== id) : [...box, id]
    setBox(next)
    saveBox(next)
  }

  return (
    <main>
      <div className="c">
        <Link className="back" to="/home">← 처음으로</Link>
        <h1 tabIndex={-1}>무슨 일에 Claude Code를 쓰나요?</h1>
        <p className="lead">하나를 고르면 그 분야 도구를 보여 드려요. 나중에 언제든 바꿀 수 있어요.</p>

        <div className="cats">
          {categories.map(c => (
            <button
              key={c.id}
              className="cat"
              data-start={c.id}
              aria-pressed={picked === c.id}
              onClick={() => setPicked(c.id)}
            >
              <b>{c.name}</b>
              <span>{c.when}</span>
            </button>
          ))}
        </div>

        {picked && starters.length > 0 && (
          <>
            <h2 style={{ marginTop: 'var(--s8)' }}>
              {categories.find(c => c.id === picked)?.name}: 처음 읽는 양이 적은 3개
            </h2>
            <div className="starter">
              {starters.map(t => (
                <div key={t.id} className="panel">
                  <h3>
                    <Link to={`/tool/${t.id}`} style={{ textDecoration: 'none' }}>{t.name}</Link>
                  </h3>
                  <p className="n">처음 읽는 양 +{fmt(t.tokens)} · 별 {fmt(t.stars)}</p>
                  <AddButton id={t.id} box={box} onToggle={toggleBox} />
                </div>
              ))}
            </div>
            <p className="note">
              시작용 추천 목록은 아직 정하지 않았어요. 지금은 같은 분야에서 처음 읽는 양이 적은 3개를 보여 주는 예시예요.
            </p>
            <div className="row-actions">
              <Link className="btn btn-p" to="/box">도구함 보기</Link>
              <Link className="btn" to={`/browse/${picked}`}>이 분야 전체 보기</Link>
            </div>
          </>
        )}
      </div>
    </main>
  )
}
