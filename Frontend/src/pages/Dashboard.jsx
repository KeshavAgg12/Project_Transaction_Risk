import './Dashboard.css'
import { useState } from 'react'
import ErrorState from '../components/ui/ErrorState.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import Segmented from '../components/ui/Segmented.jsx'
import Skeleton from '../components/ui/Skeleton.jsx'
import RecentTransactions from '../components/dashboard/RecentTransactions.jsx'
import RiskDistribution from '../components/dashboard/RiskDistribution.jsx'
import StatCard from '../components/dashboard/StatCard.jsx'
import TransactionChart from '../components/dashboard/TransactionChart.jsx'
import { useAsync } from '../hooks/useAsync.js'
import { getOverview } from '../services/analyticsService.js'
import { formatMoney, formatNumber } from '../utils/formatters.js'

const RANGES = { Today: 'today', '7 Days': '7d', '30 Days': '30d', '90 Days': '90d' }
const dash = (format) => (value) => (value === null || value === undefined ? '—' : format(value))

// [api key, label, formatter, is an increase good news?]
const KPI_CARDS = [
  ['total_transactions', 'Total Transactions', dash(formatNumber), true],
  ['total_volume', 'Transaction Volume', dash(formatMoney), true],
  ['high_risk_count', 'High Risk Transactions', dash(formatNumber), false],
  ['approval_rate', 'Approval Rate', dash((v) => `${v}%`), true],
  ['avg_risk_score', 'Average Risk Score', dash((v) => v), false],
  ['active_alerts', 'Active Alerts', dash(formatNumber), false],
]

export default function Dashboard() {
  const [rangeLabel, setRangeLabel] = useState('30 Days')
  const { data, loading, error } = useAsync(() => getOverview(RANGES[rangeLabel]), [rangeLabel])

  return (
    <>
      <PageHeader
        title="Risk Overview"
        subtitle="Monitor transaction activity and risk signals."
        actions={<Segmented label="Date range" options={Object.keys(RANGES)} value={rangeLabel} onChange={setRangeLabel} />}
      />
      {error && <ErrorState message={error} />}
      {loading && <Skeleton rows={6} />}
      {data && (
        <>
          <div className="grid kpis">
            {KPI_CARDS.map(([key, label, format, goodWhenUp]) => {
              const kpi = data.kpis[key]
              const change = kpi.change_pct ?? null
              return <StatCard key={key} label={label} value={format(kpi.value)} change={change} positive={change !== null && change >= 0 === goodWhenUp} />
            })}
          </div>
          <div className="grid two">
            <RiskDistribution data={data.daily_risk} />
            <TransactionChart data={data.daily_activity} />
          </div>
        </>
      )}
      <RecentTransactions />
    </>
  )
}
