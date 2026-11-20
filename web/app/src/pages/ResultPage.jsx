import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getTools, getRecommend, fmt, PRIORITY_LABEL } from '../api.js'
import Steps from '../components/Steps.jsx'
import Reason from '../components/Reason.jsx'

const WORK_LABEL = { bugfix: '버그 고치기', feature: '새 기능 만들기', unknown: '잘 모르겠어요' }
const SHELL_LABEL = { bash: 'bash / zsh', powershell: 'PowerShell', unknown: '잘 모르겠어요' }

function getBox() {
  try { return JSON.parse(sessionStorage.getItem('inv-box') || '[]') } catch { return [] }
}
function getAns() {
  try { return JSON.parse(sessionStorage.getItem('inv-ans') || '{}') } catch { return {} }
}

// 상황 하나의 카드: (중요한 것으로 고른 도구) + 기본 기능으로도 / 이럴 땐 깔면 더 좋아요 / 대신
function SituationCardView({ s, priority }) {
  return (
    <>
    {s.pick && (
      <div className="banner" role="status" style={{ marginBottom: 'var(--s4)' }}>
        <b>{s.pick.label}이 중요하다면 → </b>
        {s.pick.base
          ? <b>기본 기능으로 충분해요</b>
          : s.pick.tools.map((t, i) => (
              <span key={t.id}>{i > 0 && ' 또는 '}<Link to={`/tool/${t.id}`}><b>{t.name}</b></Link>{t.inBox && <span className="mute"> (이미 도구함에 있어요)</span>}</span>
            ))}
        <br />{s.pick.reason}
      </div>
    )}
    {!s.pick && PRIORITY_LABEL[priority] && (
      <p className="mute" style={{ marginTop: 0 }}>
        '{PRIORITY_LABEL[priority]}' 기준으로는 시험에서 도구 사이 차이를 확인하지 못했어요. 아래 세 칸을 보고 골라 주세요.
      </p>
    )}
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--s4)' }}>
      <div>
        <h3>기본 기능으로도</h3>
        <p>{s.base}</p>
      </div>
      <div>
        <h3>이럴 땐 깔면 더 좋아요</h3>
        <p>
          {s.tools.map((t, i) => (
            <span key={t.id}>
              {i > 0 && ' 또는 '}
              <Link to={`/tool/${t.id}`}><b>{t.name}</b></Link>
              {t.inBox && <span className="mute"> (이미 도구함에 있어요)</span>}
            </span>
          ))}
        </p>
        <p>{s.better}</p>
        {s.tools.filter(t => t.overlapWith?.length).map(t => (
          <p key={`ov-${t.id}`} className="banner" role="status" style={{ margin: 'var(--s2) 0 0' }}>
            <b>{t.name} · 도구함의 {t.overlapWith.join(', ')}와 겹쳐요.</b> 같이 켜면 비슷한 설명을 둘 다 읽어서 토큰만 늘 수 있어요.
          </p>
        ))}
        {s.tools.filter(t => t.similarTo?.length).map(t => (
          <p key={`si-${t.id}`} className="mute" style={{ margin: 'var(--s2) 0 0' }}>
            {t.name} · 도구함의 {t.similarTo.join(', ')}와 비슷한 역할이에요(상황따라). 더 깔기 전에 이미 있는 도구로 되는지 먼저 확인해 보세요.
          </p>
        ))}
      </div>
      <div>
        <h3>대신</h3>
        <p>{s.cost}</p>
      </div>
    </div>
    <p className="mute" style={{ fontSize: 13.5, marginBottom: 0 }}>
      근거: {s.review?.startsWith(s.evidence) ? s.review : `${s.evidence}${s.review ? ` · ${s.review}` : ''}`}{s.source ? ` · ${s.source}` : ''}
    </p>
    </>
  )
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

  const { pairs, remove, add, unknownCount, situation, goal } = result
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
          <dt>{goal ? '목적' : '상황'}</dt>
          <dd>{goal?.label || situation?.label || '고르지 않음'}</dd>
          <dd><Link to="/ask/situation">바꾸기</Link></dd>
          {(situation || goal) && <>
            <dt>중요한 것</dt>
            <dd>{PRIORITY_LABEL[answers.priority] || '상관없음'}</dd>
            <dd><Link to="/ask/priority">바꾸기</Link></dd>
          </>}
          <dt>주로 하는 일</dt>
          <dd>{WORK_LABEL[answers.work] || '—'}</dd>
          <dd><Link to="/ask/1">바꾸기</Link></dd>
          <dt>명령 실행</dt>
          <dd>{SHELL_LABEL[answers.shell] || '—'}</dd>
          <dd><Link to="/ask/2">바꾸기</Link></dd>
        </dl>

        {situation && (
          <section className="panel" style={{ marginTop: 'var(--s8)' }} aria-labelledby="sit-h">
            <h2 id="sit-h" style={{ marginTop: 0 }}>이 상황이라면: {situation.label}</h2>
            <SituationCardView s={situation} priority={answers.priority} />
          </section>
        )}

        {goal && (
          <section className="panel" style={{ marginTop: 'var(--s8)' }} aria-labelledby="goal-h">
            <h2 id="goal-h" style={{ marginTop: 0 }}>이 목적이라면: {goal.label}</h2>
            <p className="mute" style={{ marginTop: 0 }}>{goal.desc} · 시험한 상황 {goal.situations.length}개를 모아 봤어요.</p>
            {!PRIORITY_LABEL[answers.priority] && (
              <p className="banner" role="status">무엇이 제일 중요한지 고르면 시험 결과로 더할 것·꺼도 되는 것을 골라 드려요. <Link to="/ask/priority">중요한 것 고르기</Link></p>
            )}
            {PRIORITY_LABEL[answers.priority] && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--s4)' }}>
                {[['더하기', goal.add, '이 목적에서 고른 기준으로 더 나았던 도구가 없어요.'],
                  ['꺼도 되는 것', goal.turnOff, '시험상 꺼도 되는 도구가 도구함에 없어요.'],
                  ['그대로', goal.keep, '이미 있는 도구 중 고른 도구가 없어요.']].map(([title, items, empty]) => (
                  <div key={title}>
                    <h3>{title}</h3>
                    {items.length === 0 && <p className="mute">{empty}</p>}
                    {items.map(x => (
                      <div key={x.tool} style={{ marginBottom: 'var(--s3)' }}>
                        <Link to={`/tool/${x.tool}`}><b>{x.name}</b></Link>
                        {x.situations.map((sl, i) => <p key={i} style={{ margin: '2px 0', fontSize: 14 }}>{sl}: {x.reasons[i]}</p>)}
                        {x.warnings.map((w, i) => <p key={`w${i}`} className="warn" style={{ margin: '2px 0' }}>{w}</p>)}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            )}
            <h3 style={{ marginTop: 'var(--s6)' }}>상황별로 보기</h3>
            {goal.situations.map(c => (
              <details key={c.id} style={{ marginBottom: 'var(--s3)' }}>
                <summary><b>{c.label}</b>{c.pick ? ` → ${c.pick.base ? '기본 기능으로 충분' : c.pick.tools.map(t => t.name).join(' 또는 ')}` : ''}</summary>
                <div style={{ padding: 'var(--s3) 0 0' }}><SituationCardView s={c} priority={answers.priority} /></div>
              </details>
            ))}
            <p className="mute" style={{ fontSize: 13.5, marginBottom: 0 }}>목적별 상황 묶음은 우리 팀이 정한 것이고, 각 상황의 판단은 직접 시험 결과예요.</p>
          </section>
        )}

        <div className="split" style={{ marginTop: 'var(--s8)' }}>
          <div className="reco">
            <h2>빼면 좋은 것</h2>
            {remove.length
              ? remove.map(x => (
                  <div key={x.tool} className="panel">
                    <h3>{byId[x.tool]?.name || x.tool} 빼기</h3>
                    <p>
                      {byId[x.keep]?.name || x.keep}와 겹쳐요({x.review}{x.judged_at ? ` · 확인 ${x.judged_at}` : ''}).{' '}
                      하나만 켰을 때 잰 값으로는 처음 읽는 양이 <b className="n">{fmt(x.save)}</b>토큰 줄어요(참고값, 같이 켠 상태에서 따로 재지 않음).
                    </p>
                    <p className="mute" style={{ fontSize: 13.5 }}>지금은 토큰이 큰 쪽을 빼자고 하는 임시 규칙이에요. 상황에 맞는 쪽을 남기는 규칙은 다음 단계에서 붙여요.</p>
                    <Reason p={x} />
                  </div>
                ))
              : <div className="empty">겹치는 쌍이 없어서 뺄 것을 찾지 못했어요.</div>
            }

            <h2 style={{ marginTop: 'var(--s8)' }}>더해 볼 만한 것</h2>
            {(situation || goal) && <div className="empty">위 {goal ? '목적' : '상황'} 카드에서 직접 시험 결과로 골랐어요.</div>}
            {!(situation || goal) && <p className="mute">목적이나 상황을 고르면 시험 결과로 더할 도구를 골라 드려요. <Link to="/ask/situation">고르러 가기</Link> · 아래는 토큰 줄이기 도구 첫 시험(2026-10-18) 결과예요.</p>}
            {(situation || goal) ? null : add.length
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
