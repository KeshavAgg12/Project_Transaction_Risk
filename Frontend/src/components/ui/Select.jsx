import './Input.css'
export default function Select({ label, value, onChange, options }) {
  return (
    <select className="input box" aria-label={label} value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">{label}: all</option>
      {options.map((option) => <option key={option}>{option}</option>)}
    </select>
  )
}
