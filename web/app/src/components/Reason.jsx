// 판정 이유와 출처를 펼쳐 보는 칸. 이유가 없는 짝(확인된 정보 없음)에는 아무것도 그리지 않는다.
export default function Reason({ p }) {
  if (!p?.reason) return null
  return (
    <details className="why">
      <summary>이유 보기</summary>
      <p>{p.reason}</p>
      {p.sources?.length > 0 && <p className="src">출처: {p.sources.join(', ')}</p>}
    </details>
  )
}
