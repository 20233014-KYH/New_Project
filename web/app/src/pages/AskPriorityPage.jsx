import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Steps from '../components/Steps.jsx'
import { getSituations } from '../api.js'

// 선택지 순서·문장은 조사 결과(사람들이 도구를 고를 때 따지는 것: 토큰·한도, 정확도, 설치 수고, 안전)를 따른다
const OPTS = [
  ['accurate', '틀리지 않는 것', '결과가 정확한 게 제일 중요해요'],
  ['save', '토큰·한도 아끼기', '사용 한도가 빨리 닳는 게 걱정돼요'],
  ['simple', '설치·관리가 간단한 것', '설정할 게 많거나 계속 켜 둬야 하는 건 싫어요'],
  ['safe', '실수로 망가뜨리지 않는 것', 'DB나 파일을 잘못 바꾸면 안 돼요'],
]

function getAns() {
  try { return JSON.parse(sessionStorage.getItem('inv-ans') || '{}') } catch { return {} }
}
function saveAns(ans) {
  try { sessionStorage.setItem('inv-ans', JSON.stringify(ans)) } catch {}
}

// 질문 2: (상황을 고른 뒤) 무엇이 제일 중요한가요? 답에 따라 상황 카드에서 도구 하나를 골라 준다
export default function AskPriorityPage() {
  const saved = getAns()
  const [selected, setSelected] = useState(saved.priority ?? '')
  const [label, setLabel] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    if (!saved.situation) { navigate('/ask/1', { replace: true }); return }
    getSituations().then(list => setLabel(list.find(s => s.id === saved.situation)?.label || ''))
  }, [])

  function handleSubmit(e) {
    e.preventDefault()
    saveAns({ ...getAns(), priority: selected })
    navigate('/ask/1')
  }

  return (
    <main>
      <div className="c">
        <Steps current={2} />
        <div className="qwrap">
          <Link className="back" to="/ask/situation">← 뒤로</Link>
          <p className="qcount">질문 2 / 4</p>
          <form id="qform" onSubmit={handleSubmit} noValidate>
            <fieldset>
              <legend><h1 tabIndex={-1}>이 일을 할 때 무엇이 제일 중요해요?</h1></legend>
              {label && <p className="mute" style={{ margin: '0 0 var(--s4)' }}>고른 상황: {label}</p>}
              <div className="radios">
                {OPTS.map(([v, l, hint]) => (
                  <label key={v} className="radio">
                    <input type="radio" name="p" value={v} checked={selected === v} onChange={() => setSelected(v)} />
                    <div><b>{l}</b><span>{hint}</span></div>
                  </label>
                ))}
                <label className="radio">
                  <input type="radio" name="p" value="" checked={selected === ''} onChange={() => setSelected('')} />
                  <div><b>상관없어요</b><span>도구별 장단점을 모두 볼게요</span></div>
                </label>
              </div>
            </fieldset>
            <p className="why">왜 묻나요? 같은 상황에서도 무엇을 중요하게 보느냐에 따라 직접 시험에서 더 나았던 도구가 달라요. 그 결과로 하나를 골라 드려요.</p>
            <div className="row-actions">
              <button className="btn btn-p" type="submit">다음</button>
            </div>
          </form>
        </div>
      </div>
    </main>
  )
}
