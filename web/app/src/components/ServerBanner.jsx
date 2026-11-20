import { useEffect, useState } from 'react'

// 서버 모드(VITE_API_BASE)에서 서버에 연결하지 못하면 화면 맨 위에 안내 띠를 띄운다.
// api.js의 apiFetch가 'inv-server' 이벤트를 보내고, 다시 연결되면 띠가 사라진다.
export default function ServerBanner() {
  const [down, setDown] = useState(false)

  useEffect(() => {
    const on = e => setDown(!e.detail.ok)
    window.addEventListener('inv-server', on)
    return () => window.removeEventListener('inv-server', on)
  }, [])

  if (!down) return null
  return (
    <div role="alert" style={{ background: '#fff4e5', color: '#7a4b00', borderBottom: '1px solid #f0c98a',
      padding: '10px 16px', fontSize: 14.5, textAlign: 'center' }}>
      서버에 연결하지 못했어요. 서버가 켜져 있는지 확인해 주세요(server/app 폴더에서 <code>./gradlew bootRun</code>).
      {' '}<button type="button" onClick={() => window.location.reload()}
        style={{ background: 'none', border: 0, color: 'inherit', textDecoration: 'underline', cursor: 'pointer', font: 'inherit' }}>
        다시 시도
      </button>
    </div>
  )
}
