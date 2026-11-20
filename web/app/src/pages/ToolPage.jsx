import { useState, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getTool, getTools, getCategories, fmt } from '../api.js'
import Reason from '../components/Reason.jsx'

const KO = { overlap: 'ov', situational: 'si', complement: 'co', none: 'no', no_info: 'no' }
const KO_LABEL = { overlap: '겹침', situational: '상황따라', complement: '보완', none: '관계 없음', no_info: '확인된 정보 없음' }

function getBox() {
  try { return JSON.parse(sessionStorage.getItem('inv-box') || '[]') } catch { return [] }
}
function saveBox(ids) {
  try { sessionStorage.setItem('inv-box', JSON.stringify(ids)) } catch {}
}

export default function ToolPage() {
  const { id } = useParams()
  const [tool, setTool] = useState(null)
  const [catName, setCatName] = useState({})
  const [box, setBox] = useState(getBox)
  const [catOf, setCatOf] = useState({})

  useEffect(() => {
    getTool(id).then(setTool)
    getTools().then(ts => setCatOf(Object.fromEntries(ts.map(t => [t.id, t.category]))))
    getCategories().then(cats => {
      const map = {}
      cats.forEach(c => { map[c.id] = c.name })
      setCatName(map)
    })
  }, [id])

  function toggleBox(tid) {
    const next = box.includes(tid) ? box.filter(x => x !== tid) : [...box, tid]
    setBox(next)
    saveBox(next)
  }

  if (!tool) return <main><div className="c"><p className="mute">불러오는 중…</p></div></main>

  const inBox = box.includes(tool.id)
  const scope = tool.scope || {}
  const parts = [
    ['스킬', scope.skills],
    ['명령', scope.commands],
    ['에이전트', scope.agents],
    ['MCP 도구', scope.mcp],
    ['훅', scope.hooks_total],
  ]
  const pm = Math.max(1, ...parts.map(p => p[1] || 0))

  const samePairs = (tool.pairs || []).filter(p => !catOf[p.otherId] || catOf[p.otherId] === tool.category)
  const otherPairs = (tool.pairs || []).filter(p => catOf[p.otherId] && catOf[p.otherId] !== tool.category)
  const otherNone = otherPairs.filter(p => p.relation === 'none').length
  const clashes = (tool.pairs || []).filter(p => p.relation === 'overlap' && box.includes(p.otherId))

  return (
    <main>
      <div className="c">
        <p className="crumb">
          <Link to={`/browse/${tool.category}`}>{catName[tool.category] || ''}</Link> › {tool.name}
        </p>

        <div className="toolhead">
          <div>
            <h1 tabIndex={-1}>{tool.name}</h1>
            {tool.summary_ko
              ? <>
                  <p className="lead" style={{ marginTop: 'var(--s2)' }}>{tool.summary_ko}</p>
                  {tool.when_ko && <p style={{ margin: 'var(--s1) 0 0' }}><b>이럴 때 쓰세요</b> · {tool.when_ko}</p>}
                  <p className="mute" lang="en" style={{ fontSize: 13, margin: 'var(--s1) 0 0' }}>저장소 원문: {tool.desc_en}</p>
                  <p className="mute" style={{ fontSize: 13, margin: 0 }}>한국어 소개는 저장소 원문을 쉬운 말로 옮긴 것이에요(팀원 확인 완료).</p>
                </>
              : <>
                  <p className="lead" lang="en" style={{ marginTop: 'var(--s2)' }}>{tool.desc_en}</p>
                  <p className="mute" style={{ fontSize: 13, margin: 'var(--s1) 0 0' }}>설명은 저장소 원문(영어)이에요.</p>
                </>}
          </div>
          <button
            className={`btn ${inBox ? '' : 'btn-p'}`}
            onClick={() => toggleBox(tool.id)}
          >
            {inBox ? '도구함에서 빼기' : '도구함에 담기'}
          </button>
        </div>

        {clashes.length > 0 && (
          <div className="banner" role="status">
            <b>도구함의 {clashes.map(p => p.otherId).join(', ')}와 겹쳐요.</b> 같이 켜면 비슷한 일을 하는 설명을 둘 다 읽어요.
          </div>
        )}

        <div className="split">
          <div>
            <h2>같은 분야 도구와 같이 켜면</h2>
            {samePairs.map(p => (
              <div key={p.otherId} className="pair">
                <div>
                  <Link to={`/tool/${p.otherId}`}>{p.otherId}</Link>
                  <small>{p.review}{p.judged_at ? ` · 확인 ${p.judged_at}` : ''}</small>
                  <Reason p={p} />
                </div>
                <span className={`tag ${KO[p.relation] || 'no'}`}>{KO_LABEL[p.relation] || p.label}</span>
              </div>
            ))}
            <h2 style={{ marginTop: 'var(--s8)' }}>다른 분야 도구와 같이 켜면</h2>
            {otherPairs.filter(p => p.relation !== 'none').map(p => (
              <div key={p.otherId} className="pair">
                <div>
                  <Link to={`/tool/${p.otherId}`}>{p.otherId}</Link>
                  <small>{catName[catOf[p.otherId]] || ''} · {p.review}{p.judged_at ? ` · 확인 ${p.judged_at}` : ''}</small>
                  <Reason p={p} />
                </div>
                <span className={`tag ${KO[p.relation] || 'no'}`}>{KO_LABEL[p.relation] || p.label}</span>
              </div>
            ))}
            {otherNone > 0 && <p className="mute">나머지 다른 분야 도구 {otherNone}개와는 관계 없음으로 판정했어요.</p>}
            <p className="note">
              다른 분야 짝은 AI 두 개(Claude·Codex)가 도구 설명을 읽고 따로 판정해 맞춰 본 추정이에요(직접 시험 아님). 두 AI 의견이 다르면 이유에 둘 다 적었어요.{' '}
              <Link to="/help">판정 낱말 풀이</Link>
            </p>

            <h2 style={{ marginTop: 'var(--s12)' }}>설치와 내장 기능</h2>
            <div className="panel">설치 방법과 Claude 기본 기능과의 비교는 아직 확인하지 않았어요.</div>
          </div>

          <aside className="spec panel">
            <div className="mute" style={{ fontSize: 14 }}>처음 읽는 양(실측)</div>
            <div className="big n">
              {tool.tokens == null ? '측정 안 함' : `+${fmt(tool.tokens)}`}
            </div>
            <div className="mute" style={{ fontSize: 13, margin: 'var(--s2) 0 var(--s6)' }}>
              도구 하나만 켜고 첫 응답에서 더 읽은 토큰 · {tool.checked_at || '2026-10-18'}
            </div>

            <h2 style={{ fontSize: 16 }}>역할 범위</h2>
            {tool.scope
              ? parts.map(([k, v]) => (
                  <div key={k} className="sb-row">
                    <span>{k}</span>
                    <div className="sb-track">
                      <div className="sb-fill" style={{ width: `${(v || 0) / pm * 100}%` }} />
                    </div>
                    <span className="n">{v || 0}</span>
                  </div>
                ))
              : <p className="mute">측정하지 않아서 확인 안 됨</p>
            }

            <dl style={{ marginTop: 'var(--s6)' }}>
              <dt>저장소</dt><dd>{tool.repo}</dd>
              <dt>버전</dt><dd className="n">{tool.version || '확인 안 됨'}</dd>
              <dt>라이선스</dt><dd>{tool.license || '확인 안 됨'}</dd>
              <dt>별</dt><dd className="n">{fmt(tool.stars)}</dd>
              <dt>최근 업데이트</dt><dd className="n">{tool.pushed_at ? tool.pushed_at.slice(0, 10) : '—'}</dd>
            </dl>
          </aside>
        </div>
      </div>
    </main>
  )
}
