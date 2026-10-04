import './TransactionDetails.css'
import { Link, useParams } from 'react-router-dom'
import ErrorState from '../components/ui/ErrorState.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import Skeleton from '../components/ui/Skeleton.jsx'
import DecisionCard from '../components/transactions/DecisionCard.jsx'
import RiskBadge from '../components/transactions/RiskBadge.jsx'
import RiskFactors from '../components/transactions/RiskFactors.jsx'
import RiskScore from '../components/transactions/RiskScore.jsx'
import TransactionInfo from '../components/transactions/TransactionInfo.jsx'
import { useAsync } from '../hooks/useAsync.js'
import { getTransactionById } from '../services/transactionService.js'
import { formatDate } from '../utils/formatters.js'

export default function TransactionDetails() {
  const { id } = useParams()
  const { data: t, loading, error } = useAsync(() => getTransactionById(id), [id])

  return (
    <>
      <Link className="back-link" to="/transactions">← Transactions</Link>
      {loading && <Skeleton rows={8} />}
      {error && <ErrorState message={error} />}
      {t && (
        <>
          <PageHeader
            title={`Transaction #${t.transaction_id}`}
            subtitle={`${formatDate(t.timestamp)} · ${t.merchant_category}`}
            actions={
              <div className="score-row">
                <RiskScore score={t.risk_score} level={t.level} />
                <RiskBadge level={t.level} />
                <span className="badge plain">{t.decision.toUpperCase()}</span>
              </div>
            }
          />
          <div className="grid two">
            <TransactionInfo transaction={t} />
            <DecisionCard transaction={t} />
          </div>
          <RiskFactors contributions={t.contributions} reasons={t.reasons} />
        </>
      )}
    </>
  )
}
