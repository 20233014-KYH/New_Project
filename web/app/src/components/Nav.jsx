import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useState } from 'react'

function getBox() {
  try { return JSON.parse(sessionStorage.getItem('inv-box') || '[]') } catch { return [] }
}

export default function Nav() {
  const [q, setQ] = useState('')
  const navigate = useNavigate()
  const boxCount = getBox().length

  function handleSearch(e) {
    e.preventDefault()
    if (q.trim()) navigate(`/find?q=${encodeURIComponent(q.trim())}`)
  }

  return (
    <nav className="nav">
      <div className="c">
        <Link to="/home" className="logo">
          <span>🔧</span>
          <span>도구 인벤토리</span>
        </Link>

        <form className="hsearch" onSubmit={handleSearch}>
          <label htmlFor="nav-search" className="sr">도구 검색</label>
          <input
            id="nav-search"
            type="search"
            placeholder="도구 이름 검색…"
            value={q}
            onChange={e => setQ(e.target.value)}
          />
        </form>

        <div className="nav-links">
          <NavLink to="/start" aria-current={undefined}>처음이에요</NavLink>
          <NavLink to="/browse/1">둘러보기</NavLink>
          <Link to="/box" className="boxlink">
            도구함
            {boxCount > 0 && <span className="pill">{boxCount}</span>}
          </Link>
        </div>
      </div>
    </nav>
  )
}
