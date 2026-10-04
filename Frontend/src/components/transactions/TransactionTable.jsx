import './TransactionTable.css'
import '../ui/Table.css'
import { useNavigate } from 'react-router-dom'
import Button from '../ui/Button.jsx'
import RiskBadge from './RiskBadge.jsx'
import RiskScore from './RiskScore.jsx'
import { formatDate, formatMoney } from '../../utils/formatters.js'

// variant="recent" is the compact dashboard table; "full" adds the actions column.
export default function TransactionTable({ rows, variant = 'full' }) {
  const navigate = useNavigate()
  const full = variant === 'full'
  const open = (id) => navigate(`/transactions/${id}`)

  const headers = ['Transaction ID', 'Timestamp', 'Customer', 'Amount', 'Payment Method', 'Distance (km)', 'Risk Score', 'Risk Level', 'Decision']
  if (full) headers.push('Actions')

  return (
    <div className="tablewrap">
      <table>
        <thead>
          <tr>{headers.map((header) => <th key={header}>{header}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((t) => (
            <tr key={t.transaction_id} tabIndex={0} onClick={() => open(t.transaction_id)} onKeyDown={(e) => e.key === 'Enter' && open(t.transaction_id)}>
              <td><b>{t.transaction_id}</b></td>
              <td>{formatDate(t.timestamp)}</td>
              <td>{t.customer_id}</td>
              <td>{formatMoney(t.amount)}</td>
              <td>{t.payment_method}</td>
              <td>{Math.round(t.distance_from_home_km)}</td>
              <td><RiskScore score={t.risk_score} level={t.level} /></td>
              <td><RiskBadge level={t.level} /></td>
              <td>{t.decision}</td>
              {full && (
                <td onClick={(e) => e.stopPropagation()}>
                  <Button to={`/transactions/${t.transaction_id}`}>View</Button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
