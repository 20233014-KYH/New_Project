import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getTools, getCategories, judgeBox, fmt } from '../api.js'
import Steps from '../components/Steps.jsx'

const KO = { overlap: 'ov', situational: 'si', complement: 'co', none: 'no', no_info: 'no' }
const KO_LABEL = { overlap: '겹침', situational: '상황따라', complement: '보완', none: '관계 없음', no_info: '확인된 정보 없음' }
const DEMO_IDS = ['superpowers', 'ecc', 'caveman']

function getBox() {
  try { return JSON.parse(sessionStorage.getItem('inv-box') || '[]') } catch { return [] }
}
function saveBox(ids) {
  try { sessionStorage.setItem('inv-box', JSON.stringify(ids)) } catch {}
}

export default function BoxPage() {
  const [box, setBox] = useState(getBox)
  const [byId, setById] = useState({})
  const [categories, setCategories] = useState([])
  const [pairs, setPairs] = useState([])
  const navigate = useNavigate()

  useEffect(() => {
    getTools().then(tools => {
      const map = {}
      tools.forEach(t => { map[t.id] = t })
      setById(map)
    })
    getCategories().then(setCategories)
  }, [])

  useEffect(() => {
    if (box.length < 2) { setPairs([]); return }
    judgeBox(box).then(setPairs)
  }, [box])

  function toggleBox(id) {
    const next = box.includes(id) ? box.filter(x => x !== id) : [...box, id]
    setBox(next)
    saveBox(next)
  }

  function clearBox() {
    saveBox([])
    setBox([])
  }

  function fillDemo() {
    saveBox(DEMO_IDS)
    setBox(DEMO_IDS)
  }

  const totalTokens = box.reduce((s, id) => s + (byId[id]?.tokens || 0), 0)
  const overlapCount = pairs.filter(p => p.relation === 'overlap').length

  if (!box.length) {
    return (
      <main>
        <div className="c">
          <Steps current={1} />
          <h1 tabIndex={-1}>내 도구함</h1>
          <p className="lead">지금 켜 둔 도구를 담으면, 같이 켰을 때 처음 읽는 양과 겹치는 쌍을 보여 드려요.</p>
          <div className="empty">
            <b style={{ color: 'var(--text)' }}>아직 담은 도구가 없어요.</b><br />
            이름을 알면 위 검색창에, 모르면{' '}
            <Link to="/start">하는 일로 고르기</Link>나{' '}
            <Link to="/browse/1">분야별 둘러보기</Link>에서 담으세요.
            <div className="row-actions" style={{ marginTop: 'var(--s4)' }}>
              <button className="btn btn-sm" onClick={fillDemo}>예시 3개로 채워 보기</button>
            </div>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main>
      <div className="c">
        <Steps current={1} />
        <h1 tabIndex={-1}>내 도구함</h1>
        <p className="lead">담은 도구를 같이 켰을 때를 미리 봐요. 다 담았으면 조건 두 가지에 답해 주세요.</p>

        <div className="status">
          <span>도구함 <b className="n">{box.length}</b>개</span>
          <span className="n">같이 켜면 최대 +{fmt(totalTokens)}토큰</span>
          {overlapCount > 0 && <span style={{ color: 'var(--accent)', fontWeight: 600 }}>겹침 {overlapCount}쌍</span>}
        </div>

        <div className="split">
          <div>
            <h2>분야별로 담은 도구</h2>
            <div className="slots">
              {categories.map(c => {
                const inC = box.filter(id => byId[id]?.category === c.id)
                return (
                  <div key={c.id} className="slot">
                    <div className="slot-name">{c.name}</div>
                    <div className="slot-tools">
                      {inC.length
                        ? inC.map(id => (
                            <div key={id} className="slot-tool">
                              <Link to={`/tool/${id}`}>{byId[id]?.name || id}</Link>
                              <span>
                                <span className="n mute" style={{ fontSize: 14 }}>
                                  {byId[id]?.tokens == null ? '측정 안 함' : `+${fmt(byId[id].tokens)}`}
                                </span>{' '}
                                <button
                                  className="add"
                                  aria-pressed="true"
                                  aria-label={`${byId[id]?.name || id} 빼기`}
                                  onClick={() => toggleBox(id)}
                                >빼기</button>
                              </span>
                            </div>
                          ))
                        : <span className="slot-empty">비어 있음 · <Link to={`/browse/${c.id}`}>이 분야 둘러보기</Link></span>
                      }
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          <div>
            <h2>쌍마다 판정</h2>
            {pairs.length === 0
              ? <p className="mute">도구가 하나라 비교할 쌍이 없어요.</p>
              : pairs.map(p => (
                  <div key={`${p.a}-${p.b}`} className="pair">
                    <div>
                      {byId[p.a]?.name || p.a} × {byId[p.b]?.name || p.b}
                      <small>{p.review}</small>
                    </div>
                    <span className={`tag ${KO[p.relation] || 'no'}`}>{KO_LABEL[p.relation] || p.label}</span>
                  </div>
                ))
            }
            <p className="note" style={{ marginTop: 'var(--s4)' }}>
              "확인된 정보 없음"은 안전하다는 뜻이 아니에요. <Link to="/help">낱말 풀이</Link>
            </p>
          </div>
        </div>

        <div className="row-actions">
          <Link className="btn btn-p" to="/ask/1">다음: 조건 두 가지 →</Link>
          <button className="btn" onClick={clearBox}>도구함 비우기</button>
        </div>
      </div>
    </main>
  )
}
