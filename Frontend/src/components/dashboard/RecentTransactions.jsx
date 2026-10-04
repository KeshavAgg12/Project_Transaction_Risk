import Card from '../ui/Card.jsx'
import ErrorState from '../ui/ErrorState.jsx'
import Skeleton from '../ui/Skeleton.jsx'
import TransactionTable from '../transactions/TransactionTable.jsx'
import { useAsync } from '../../hooks/useAsync.js'
import { getTransactions } from '../../services/transactionService.js'

export default function RecentTransactions() {
  const { data, loading, error } = useAsync(() => getTransactions({ sort: 'risk', page_size: 8 }))
  if (error) return <ErrorState message={error} />

  return (
    <Card title="Highest-risk transactions">
      {loading ? <Skeleton /> : <TransactionTable variant="recent" rows={data.data} />}
    </Card>
  )
}
