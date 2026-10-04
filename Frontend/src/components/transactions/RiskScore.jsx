import './RiskScore.css'
export default function RiskScore({ score, level }) {
  return (
    <span className={level} aria-label={`Risk score ${score} of 100`}>
      <span className="bar"><i style={{ width: `${score}%` }} /></span>
      <b>{score}</b> / 100
    </span>
  )
}
