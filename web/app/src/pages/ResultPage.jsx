import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getTools, getRecommend, fmt } from '../api.js'
import Steps from '../components/Steps.jsx'

const WORK_LABEL = { bugfix: '버그 고치기', feature: '새 기능 만들기', unknown: '잘 모르겠어요' }
const SHELL_LABEL = { bash: 'bash / zsh', powershell: 'PowerShell', unknown: '잘 모르겠어요' }

function getBox() {
  try { return JSON.parse(sessionStorage.getItem('inv-box') || '[]') } catch { return [] }
}
function getAns() {
  try { return JSON.parse(sessionStorage.getItem('inv-ans') || '{}') } catch { return {} }
}

export default function ResultPage() {
  const [box] = useState(getBox)
  const [answers] = useState(getAns)
  const [byId, setById] = useState({})
  const [result, setResult] = useState(null)

  useEffect(() => {
    getTools().then(tools => {
      const map = {}
      tools.forEach(t => { map[t.id] = t })
      setById(map)
    })
  }, [])

  useEffect(() => {
    if (!box.length || !Object.keys(byId).length) return
    getRecommend(box, answers).then(setResult)
  }, [box, byId, answers])

  if (!box.length) {
    return (
      <main>
        <div className="c">
          <Steps current={3} />
          <h1 tabIndex={-1}>결과</h1>
          <div className="empty">도구함이 비어 있어요. <Link to="/home">도구를 담고</Link> 다시 와 주세요.</div>
        </div>
      </main>
    )
  }

  if (!result) return <main><div className="c"><Steps current={3} /><p className="mute">계산 중…</p></div></main>

  const { pairs, remove, add, unknownCount } = result
  const judgedCount = pairs.length - unknownCount

  return (
    <main>
      <div className="c">
        <Steps current={3} />
        <h1 tabIndex={-1}>결과</h1>
        <p className="lead">
          담은 도구 {box.length}개, 판정한 쌍 {judgedCount}개, 확인된 정보 없는 쌍 {unknownCount}개를 기준으로 했어요.
        </p>

        <dl className="check">
          <dt>담은 도구</dt>
          <dd>{box.map(id => byId[id]?.name || id).join(', ')}</dd>
          <dd><Link to="/box">바꾸기</Link></dd>
          <dt>주로 하는 일</dt>
          <dd>{WORK_LABEL[answers.work] || '—'}</dd>
          <dd><Link to="/ask/1">바꾸기</Link></dd>
          <dt>명령 실행</dt>
          <dd>{SHELL_LABEL[answers.shell] || '—'}</dd>
          <dd><Link to="/ask/2">바꾸기</Link></dd>
        </dl>

        <div className="split" style={{ marginTop: 'var(--s8)' }}>
          <div className="reco">
            <h2>빼면 좋은 것</h2>
            {remove.length
              ? remove.map(x => (
                  <div key={x.tool} className="panel">
                    <h3>{byId[x.tool]?.name || x.tool} 빼기</h3>
                    <p>
                      {byId[x.keep]?.name || x.keep}와 겹쳐요({x.review}).{' '}
                      빼면 처음 읽는 양 <b className="n">−{fmt(x.save)}</b>(계산).
                    </p>
                  </div>
                ))
              : <div className="empty">겹치는 쌍이 없어서 뺄 것을 찾지 못했어요.</div>
            }

            <h2 style={{ marginTop: 'var(--s8)' }}>더해 볼 만한 것</h2>
            {add.length
              ? add.map(x => (
                  <div key={x.tool} className="panel">
                    <h3>{byId[x.tool]?.name || x.tool}</h3>
                    <p>{x.effect}</p>
                    {x.warnings.map((w, i) => (
                      <p key={i} className="warn">{w}</p>
                    ))}
                    {!x.warnings.length && <p className="mute">주의: {x.caution}</p>}
                    {x.unknown.length > 0 && (
                      <p className="mute">{x.unknown.map(id => byId[id]?.name || id).join(', ')}와는 아직 판정하지 않았어요.</p>
                    )}
                    <p>
                      <span className={`tag ${x.blocked || x.warnings.length ? 'ov' : 'si'}`}>{x.verdict}</span>{' '}
                      <span className="mute" style={{ fontSize: 13 }}>직접 시험 · {x.date}</span>
                    </p>
                  </div>
                ))
              : <div className="empty">시험한 후보가 이미 도구함에 있어요.</div>
            }
          </div>

          <aside className="panel">
            <h2 style={{ fontSize: 16 }}>이렇게 골랐어요</h2>
            <p className="mute" style={{ fontSize: 14.5 }}>
              1. 쌍마다 저장된 판정을 찾아요.<br />
              2. 겹치는 쌍은 처음 읽는 양이 큰 쪽을 빼자고 해요.<br />
              3. 더하기는 직접 시험해서 효과를 잰 도구만 보여 주고, 답하신 조건에 걸리는 주의를 붙여요.
            </p>
            <p className="mute" style={{ fontSize: 13.5 }}>
              도움말이며 보증이 아니에요. 실제로 빼기 전에 그 도구로만 하던 일이 있는지 확인하세요.
            </p>
          </aside>
        </div>
      </div>
    </main>
  )
}
