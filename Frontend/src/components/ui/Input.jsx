import './Input.css'
export default function Input({ label, ...props }) {
  return <input className="input box" aria-label={label} placeholder={label} {...props} />
}
