import './RiskFactors.css'
import Card from '../ui/Card.jsx'

const label = (key) => key.replaceAll('_', ' ')

export default function RiskFactors({ contributions, reasons }) {
  const entries = Object.entries(contributions ?? {}).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
  const largest = Math.max(...entries.map(([, value]) => Math.abs(value)), 0.0001)

  return (
    <Card title="Risk assessment">
      <p className="sub tight">Model contributions (log-odds, read as relative size). Red raises the score, green lowers it.</p>
      {entries.length === 0 && <p className="sub">No model contributions stored for this transaction.</p>}
      {entries.map(([name, value]) => (
        <div className="contrib" key={name}>
          <span>{label(name)}</span>
          <span className="contrib-track">
            <i className={value >= 0 ? 'raises' : 'lowers'} style={{ width: `${(Math.abs(value) / largest) * 100}%` }} />
          </span>
          <span>{value.toFixed(2)}</span>
        </div>
      ))}
      <h3 className="rules-title">Triggered rules</h3>
      {reasons.length === 0 && <p className="sub">No rules triggered.</p>}
      <div className="rules">{reasons.map((rule) => <span key={rule} className="badge plain">{rule}</span>)}</div>
    </Card>
  )
}
