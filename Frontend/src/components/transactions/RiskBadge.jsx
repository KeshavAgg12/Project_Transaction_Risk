import './RiskBadge.css'
import { AlertTriangle, CheckCircle2, OctagonX, ShieldAlert } from 'lucide-react'

const ICONS = { LOW: CheckCircle2, MEDIUM: AlertTriangle, HIGH: ShieldAlert, CRITICAL: OctagonX }

// Icon + text label so risk is never communicated by color alone.
export default function RiskBadge({ level }) {
  const Icon = ICONS[level]
  return (
    <span className={`badge ${level}`}>
      <Icon size={12} aria-hidden />
      {level}
    </span>
  )
}
