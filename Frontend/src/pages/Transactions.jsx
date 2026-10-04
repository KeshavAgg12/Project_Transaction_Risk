import Card from '../components/ui/Card.jsx'
import ErrorState from '../components/ui/ErrorState.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import Skeleton from '../components/ui/Skeleton.jsx'
import Pagination from '../components/transactions/Pagination.jsx'
import TransactionFilters from '../components/transactions/TransactionFilters.jsx'
import TransactionTable from '../components/transactions/TransactionTable.jsx'
import { useTransactions } from '../hooks/useTransactions.js'

export default function Transactions() {
  const tx = useTransactions()

  return (
    <>
      <PageHeader title="Transactions" subtitle="Search, filter and investigate scored transactions." />
      <TransactionFilters filters={tx.filters} onChange={tx.updateFilter} />
      <Card>
        {tx.error && <ErrorState message={tx.error} />}
        {tx.loading && <Skeleton rows={8} />}
        {!tx.loading && !tx.error && tx.total === 0 && (
          <p className="sub">No transactions match these filters. Clear a filter to see more.</p>
        )}
        {!tx.loading && tx.total > 0 && (
          <>
            <TransactionTable rows={tx.rows} />
            <Pagination total={tx.total} page={tx.page} pages={tx.pages} onChange={tx.setPage} />
          </>
        )}
      </Card>
    </>
  )
}
