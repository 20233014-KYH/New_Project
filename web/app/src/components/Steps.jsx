import { Link } from 'react-router-dom'

const STEPS = [
  { label: '도구 담기', href: '/box' },
  { label: '조건 답하기', href: '/ask/1' },
  { label: '결과 보기', href: '/result' },
]

export default function Steps({ current }) {
  return (
    <ol className="steps">
      {STEPS.map((s, i) => {
        const n = i + 1
        const done = n < current
        const active = n === current
        return (
          <li key={n} className={done ? 'done' : ''} aria-current={active ? 'step' : undefined}>
            {active ? s.label : <Link to={s.href}>{s.label}</Link>}
          </li>
        )
      })}
    </ol>
  )
}
