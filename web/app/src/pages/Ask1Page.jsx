import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Steps from '../components/Steps.jsx'

const OPTS = [
  ['bugfix', '버그 고치기', '오류 메시지를 보고 원인을 찾아 고쳐요'],
  ['feature', '새 기능 만들기', '기획이나 설명을 주고 코드를 짜요'],
  ['unknown', '잘 모르겠어요', '둘 다 하거나 딱히 정해져 있지 않아요'],
]

function getAns() {
  try { return JSON.parse(sessionStorage.getItem('inv-ans') || '{}') } catch { return {} }
}
function saveAns(ans) {
  try { sessionStorage.setItem('inv-ans', JSON.stringify(ans)) } catch {}
}

export default function Ask1Page() {
  const saved = getAns()
  const [selected, setSelected] = useState(saved.work || '')
  const [error, setError] = useState(false)
  const navigate = useNavigate()

  function handleSubmit(e) {
    e.preventDefault()
    if (!selected) { setError(true); return }
    const ans = { ...getAns(), work: selected }
    saveAns(ans)
    navigate('/ask/2')
  }

  return (
    <main>
      <div className="c">
        <Steps current={2} />
        <div className="qwrap">
          <Link className="back" to="/box">← 뒤로</Link>
          <p className="qcount">질문 1 / 2</p>
          <form id="qform" onSubmit={handleSubmit} noValidate>
            <fieldset>
              <legend><h1 tabIndex={-1}>Claude Code로 주로 어떤 일을 하나요?</h1></legend>
              <div className="radios">
                {OPTS.map(([v, label, hint]) => (
                  <label key={v} className="radio">
                    <input
                      type="radio"
                      name="a"
                      value={v}
                      checked={selected === v}
                      onChange={() => { setSelected(v); setError(false) }}
                    />
                    <div>
                      <b>{label}</b>
                      <span>{hint}</span>
                    </div>
                  </label>
                ))}
              </div>
            </fieldset>
            <p className="why">왜 묻나요? 버그를 고칠 때 도구에 따라 디버깅 절차를 건너뛰는 경우가 있어서 주의를 붙여 드려요.</p>
            {error && (
              <p className="err" role="alert">하나를 골라 주세요. 모르면 "잘 모르겠어요"를 고르세요.</p>
            )}
            <div className="row-actions">
              <button className="btn btn-p" type="submit">다음</button>
            </div>
          </form>
        </div>
      </div>
    </main>
  )
}
