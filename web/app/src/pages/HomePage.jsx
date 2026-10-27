import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { searchTools, getCategories, fmt } from '../api.js'

const HIGHLIGHT = {
  a: 'superpowers', b: 'ecc',
  text: '같은 과제 27번: 결과는 모두 성공, 둘 다 켜면 토큰 약 1.9배·시간 약 1.5배. ECC의 겹치는 스킬은 한 번도 안 쓰임.',
  date: '2026-10-17',
}
const DEMO_IDS = ['superpowers', 'ecc', 'caveman']

function getBox() {
  try { return JSON.parse(sessionStorage.getItem('inv-box') || '[]') } catch { return [] }
}
function saveBox(ids) {
  try { sessionStorage.setItem('inv-box', JSON.stringify(ids)) } catch {}
}

export default function HomePage() {
  const [q, setQ] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [box, setBox] = useState(getBox)
  const [allTools, setAllTools] = useState([])
  const [toolCount, setToolCount] = useState(0)
  const [catName, setCatName] = useState({})
  const inputRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    searchTools('').then(tools => {
      setAllTools(tools)
      setToolCount(tools.length)
    })
    getCategories().then(cats => {
      const map = {}
      cats.forEach(c => { map[c.id] = c.name })
      setCatName(map)
    })
  }, [])

  useEffect(() => {
    if (!q.trim()) { setSuggestions([]); return }
    searchTools(q).then(res => setSuggestions(res.slice(0, 6)))
  }, [q])

  function toggleBox(id) {
    const next = box.includes(id) ? box.filter(x => x !== id) : [...box, id]
    setBox(next)
    saveBox(next)
  }

  function fillDemo() {
    saveBox(DEMO_IDS)
    setBox(DEMO_IDS)
    navigate('/box')
  }

  const measured = allTools.filter(t => t.tokens != null).length

  return (
    <main>
      <div className="c">
        <div className="hero">
          <div>
            <h1 tabIndex={-1}>쓰는 도구를 담으면,<br />겹치는 것을 찾아 드려요</h1>
            <p className="lead">
              Claude Code 플러그인·스킬·MCP {toolCount}개 중 {measured}개를 직접 켜서 처음 읽는 토큰을 쟀어요. 비슷한 일을 하는 도구를 같이 켜면 토큰만 늘 수 있어요.
            </p>

            <div className="bigsearch">
              <label htmlFor="q">지금 쓰는 도구 이름을 입력하세요</label>
              <input
                id="q"
                ref={inputRef}
                type="search"
                role="combobox"
                aria-expanded={suggestions.length > 0}
                aria-controls="sugg"
                aria-autocomplete="list"
                placeholder="예: superpowers"
                autoComplete="off"
                value={q}
                onChange={e => setQ(e.target.value)}
              />
              {suggestions.length > 0 && (
                <ul className="sugg" id="sugg" role="listbox" aria-label="찾은 도구">
                  {suggestions.map((t, i) => (
                    <li key={t.id} role="option" id={`sg-${i}`} aria-selected="false">
                      <div>
                        <Link to={`/tool/${t.id}`}>{t.name}</Link>
                        <small>
                          {catName[t.category] || ''} ·{' '}
                          {t.tokens == null ? '측정 안 함' : `처음 읽는 양 +${fmt(t.tokens)}`}
                        </small>
                      </div>
                      <button
                        className="add"
                        aria-pressed={box.includes(t.id)}
                        onClick={() => toggleBox(t.id)}
                      >
                        {box.includes(t.id) ? '빼기' : '담기'}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              <p className="hint">
                찾은 도구 옆 <b>담기</b>를 누르세요. 먼저 구경만 하려면{' '}
                <button type="button" onClick={fillDemo}>예시 3개로 채워 보기</button>
              </p>
            </div>

            <div className="paths">
              <Link className="path" to="/start">
                <b>무슨 도구가 있는지 몰라요</b>
                <span>하는 일을 고르면 도구를 보여 드려요</span>
              </Link>
              <Link className="path" to="/browse/1">
                <b>분야별로 둘러볼게요</b>
                <span>6개 분야, {toolCount}개 도구</span>
              </Link>
            </div>
          </div>

          <div className="panel">
            <h2>이렇게 쓰세요</h2>
            <ol className="how">
              <li>
                <span className="num">1</span>
                <div>
                  <b>도구 담기</b>
                  <p>지금 켜 둔 도구를 검색하거나 둘러보고 담아요.</p>
                </div>
              </li>
              <li>
                <span className="num">2</span>
                <div>
                  <b>두 가지 답하기</b>
                  <p>하는 일과 명령을 실행하는 곳만 물어봐요.</p>
                </div>
              </li>
              <li>
                <span className="num">3</span>
                <div>
                  <b>결과 보기</b>
                  <p>뺄 것과 더해 볼 것을 근거와 함께 보여 드려요.</p>
                </div>
              </li>
            </ol>
            <details>
              <summary>"처음 읽는 양"이 뭐예요?</summary>
              <p>도구를 켜면 Claude가 대화를 시작할 때 도구 설명을 먼저 읽어요. 그만큼 매번 토큰을 더 써요. 도구 하나만 켜고 첫 응답에서 늘어난 토큰을 쟀어요.</p>
            </details>
          </div>
        </div>

        <section className="fact">
          <div>
            <div className="mute" style={{ fontSize: 14 }}>직접 시험 · {HIGHLIGHT.date}</div>
            <div className="big n">약 1.9배</div>
            <div className="mute" style={{ fontSize: 14 }}>둘 다 켰을 때 토큰</div>
          </div>
          <div>
            <h2>{HIGHLIGHT.a}와 {HIGHLIGHT.b}를 같이 켜면</h2>
            <p className="mute" style={{ margin: 0 }}>{HIGHLIGHT.text}</p>
            <p style={{ margin: 'var(--s4) 0 0' }}>
              <Link to={`/tool/${HIGHLIGHT.b}`}>{HIGHLIGHT.b} 자세히 보기</Link>
            </p>
          </div>
        </section>
      </div>
    </main>
  )
}
