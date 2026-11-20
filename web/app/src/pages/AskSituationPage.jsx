import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Steps from '../components/Steps.jsx'
import { getSituations, getCategories } from '../api.js'

function getAns() {
  try { return JSON.parse(sessionStorage.getItem('inv-ans') || '{}') } catch { return {} }
}
function saveAns(ans) {
  try { sessionStorage.setItem('inv-ans', JSON.stringify(ans)) } catch {}
}

// 질문 1: 어떤 상황에서 도구를 찾나요? (상황별 추천 규칙 situation_rules.csv의 선택지)
export default function AskSituationPage() {
  const [situations, setSituations] = useState([])
  const [catName, setCatName] = useState({})
  const [selected, setSelected] = useState(getAns().situation ?? '')
  const navigate = useNavigate()

  useEffect(() => {
    getSituations().then(setSituations)
    getCategories().then(cats => setCatName(Object.fromEntries(cats.map(c => [c.id, c.name]))))
  }, [])

  function handleSubmit(e) {
    e.preventDefault()
    saveAns({ ...getAns(), situation: selected })
    navigate('/ask/1')
  }

  const groups = [...new Set(situations.map(s => s.category))].sort((a, b) => a - b)  // 분야 번호 순서(규칙 파일 순서와 상관없이)

  return (
    <main>
      <div className="c">
        <Steps current={2} />
        <div className="qwrap">
          <Link className="back" to="/box">← 뒤로</Link>
          <p className="qcount">질문 1 / 3</p>
          <form id="qform" onSubmit={handleSubmit} noValidate>
            <fieldset>
              <legend><h1 tabIndex={-1}>어떤 상황에서 도구를 찾고 있나요?</h1></legend>
              {groups.map(cat => (
                <div key={cat} style={{ marginTop: 'var(--s4)' }}>
                  <p className="mute" style={{ margin: '0 0 var(--s2)' }}>{catName[cat] || ''}</p>
                  <div className="radios">
                    {situations.filter(s => s.category === cat).map(s => (
                      <label key={s.id} className="radio">
                        <input type="radio" name="s" value={s.id} checked={selected === s.id} onChange={() => setSelected(s.id)} />
                        <div><b>{s.label}</b></div>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
              <div className="radios" style={{ marginTop: 'var(--s4)' }}>
                <label className="radio">
                  <input type="radio" name="s" value="" checked={selected === ''} onChange={() => setSelected('')} />
                  <div><b>여기에 없어요 / 건너뛸게요</b><span>담은 도구끼리의 겹침만 볼게요</span></div>
                </label>
              </div>
            </fieldset>
            <p className="why">왜 묻나요? 상황마다 기본 기능으로 어디까지 되는지, 어떤 오픈소스를 깔면 더 좋은지 직접 시험한 결과로 알려 드려요. 지금은 시험을 마친 분야의 상황만 있어요.</p>
            <div className="row-actions">
              <button className="btn btn-p" type="submit">다음</button>
            </div>
          </form>
        </div>
      </div>
    </main>
  )
}
