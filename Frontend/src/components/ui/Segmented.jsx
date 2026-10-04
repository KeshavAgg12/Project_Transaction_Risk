import './Segmented.css'
export default function Segmented({ label, options, value, onChange }) {
  return (
    <div className="seg" role="group" aria-label={label}>
      {options.map((option) => (
        <button key={option} className={option === value ? 'on' : ''} onClick={() => onChange(option)}>
          {option}
        </button>
      ))}
    </div>
  )
}
