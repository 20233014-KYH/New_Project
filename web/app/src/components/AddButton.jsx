export default function AddButton({ id, box, onToggle }) {
  const inBox = box.includes(id)
  return (
    <button
      className="add"
      aria-pressed={inBox}
      onClick={() => onToggle(id)}
    >
      {inBox ? '빼기' : '담기'}
    </button>
  )
}
