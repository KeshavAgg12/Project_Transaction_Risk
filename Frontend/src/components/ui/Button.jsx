import './Button.css'
import { Link } from 'react-router-dom'

export default function Button({ to, variant = 'default', children, ...props }) {
  const className = `btn ${variant === 'primary' ? 'primary' : ''}`
  if (to) return <Link className={className} to={to} {...props}>{children}</Link>
  return <button className={className} {...props}>{children}</button>
}
