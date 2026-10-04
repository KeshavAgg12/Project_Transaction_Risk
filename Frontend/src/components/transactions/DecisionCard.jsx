import './DecisionCard.css'
import Card from '../ui/Card.jsx'

export default function DecisionCard({ transaction: t }) {
  return (
    <Card title="Decision">
      <p className="score-big">{t.risk_score}</p>
      <p className="flush">Decision: <b>{t.decision}</b></p>
      <p className="sub">Scored by model {t.model_version}.</p>
      <div className="demo">Demo model trained on synthetic data. Scores are not real-world fraud probabilities.</div>
    </Card>
  )
}
