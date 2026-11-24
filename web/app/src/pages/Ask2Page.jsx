import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Steps from '../components/Steps.jsx'

const OPTS = [
  ['bash', 'bash / zsh (macOS·Linux)', 'Mac이나 Linux에서 터미널을 써요'],
  ['powershell', 'PowerShell (Windows)', 'Windows에서 PowerShell을 써요'],
  ['unknown', '잘 모르겠어요', '확실하지 않아요'],
]

function getAns() {
  try { return JSON.parse(sessionStorage.getItem('inv-ans') || '{}') } catch { return {} }
}
function saveAns(ans) {
  try { sessionStorage.setItem('inv-ans', JSON.stringify(ans)) } catch {}
}

export default function Ask2Page() {
  const saved = getAns()
  const [selected, setSelected] = useState(saved.shell || '')
  const [error, setError] = useState(false)
  const navigate = useNavigate()

  function handleSubmit(e) {
    e.preventDefault()
    if (!selected) { setError(true); return }
    const ans = { ...getAns(), shell: selected }
    saveAns(ans)
    navigate('/result')
  }

  return (
    <main>
      <div className="c">
        <Steps current={2} />
        <div className="qwrap">
          <Link className="back" to="/ask/1">← 뒤로</Link>
          <p className="qcount">질문 2 / 2</p>
          <form id="qform" onSubmit={handleSubmit} noValidate>
            <fieldset>
              <legend><h1 tabIndex={-1}>Claude Code가 명령을 실행할 때 어떤 곳을 써요?</h1></legend>
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
            <p className="why">왜 묻나요? 일부 도구는 PowerShell에서 작동하지 않는 경우가 있어서 주의를 붙여 드려요.</p>
            {error && (
              <p className="err" role="alert">하나를 골라 주세요. 모르면 "잘 모르겠어요"를 고르세요.</p>
            )}
            <div className="row-actions">
              <button className="btn btn-p" type="submit">결과 보기</button>
            </div>
          </form>
        </div>
      </div>
    </main>
  )
}
