import { useState, useEffect } from 'react'
import { getTools } from '../api.js'

export default function HelpPage() {
  const [toolCount, setToolCount] = useState(0)

  useEffect(() => {
    getTools().then(t => setToolCount(t.length))
  }, [])

  return (
    <main>
      <div className="c">
        <h1 tabIndex={-1}>용어 풀이</h1>
        <p className="lead">화면에 나오는 낱말을 한곳에 모았어요.</p>

        <dl className="terms">
          <dt>처음 읽는 양</dt>
          <dd>도구를 켜면 대화를 시작할 때 Claude가 도구 설명을 먼저 읽어요. 도구 하나만 켜고 첫 응답에서 늘어난 토큰을 쟀어요(실측).</dd>

          <dt>최대 +n토큰</dt>
          <dd>하나씩 잰 값을 더한 계산이에요. 실제로 같이 켜면 이보다 적거나 같아요.</dd>

          <dt><span className="tag ov">겹침</span></dt>
          <dd>비슷한 일을 하는 도구 쌍이에요. 같이 켜면 설명을 둘 다 읽어서 토큰만 늘 수 있어요.</dd>

          <dt><span className="tag si">상황따라</span></dt>
          <dd>하는 일에 따라 둘 다 쓸모 있거나 하나만 쓰일 수 있어요.</dd>

          <dt><span className="tag co">보완</span></dt>
          <dd>서로 다른 일을 해서 같이 쓰면 좋아요.</dd>

          <dt><span className="tag no">확인된 정보 없음</span></dt>
          <dd>아직 판정하지 않은 쌍이에요. 안전하다는 뜻이 아니에요.</dd>

          <dt>직접 시험 / 사람 검토</dt>
          <dd>직접 시험은 같은 과제를 여러 번 돌려 잰 것, 사람 검토는 팀원이 기능을 읽고 판정한 것이에요.</dd>
        </dl>

        <h2 style={{ marginTop: 'var(--s12)' }}>자주 묻는 질문</h2>

        <details>
          <summary>제 도구가 목록에 없어요</summary>
          <p>지금은 직접 잰 {toolCount}개만 있어요. 목록에 없는 도구는 판정하지 않아요.</p>
        </details>

        <details>
          <summary>추천대로 빼도 되나요?</summary>
          <p>도움말이에요. 빼기 전에 그 도구로만 하던 일이 있는지 확인하세요.</p>
        </details>

        <details>
          <summary>제가 담은 도구는 어디에 저장되나요?</summary>
          <p>이 브라우저 탭 안에만 있어요. 탭을 닫으면 사라지고, 서버로 보내지 않아요.</p>
        </details>
      </div>
    </main>
  )
}
