import './StatCard.css'

// change = percent vs previous period (null when there is nothing to compare).
// positive = whether that direction is good news, which decides the color.
export default function StatCard({ label, value, change, positive }) {
  return (
    <div className="card kpi">
      <div className="l">{label}</div>
      <div className="v">{value}</div>
      {change !== null && change !== undefined && (
        <div className={`delta ${positive ? 'up' : 'down'}`}>
          {change < 0 ? '▼' : '▲'} {Math.abs(change)}% <span className="delta-note">vs previous period</span>
        </div>
      )}
    </div>
  )
}
