import { useEffect, useState } from 'react'
import { getTransactions } from '../services/transactionService.js'
import { useAsync } from './useAsync.js'

const PAGE_SIZE = 10
const DEFAULT_FILTERS = { search: '', level: '', decision: '', payment_method: '', sort: 'time' }

export function useTransactions() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  // Wait 300ms after typing stops so we do not call the API on every keystroke.
  useEffect(() => {
    const timer = setTimeout(() => setSearch(filters.search), 300)
    return () => clearTimeout(timer)
  }, [filters.search])

  const updateFilter = (key, value) => {
    setFilters((previous) => ({ ...previous, [key]: value }))
    setPage(1)
  }

  const params = { ...filters, search, page, page_size: PAGE_SIZE }
  const { data, loading, error } = useAsync(() => getTransactions(params), [JSON.stringify(params)])

  return {
    loading, error, filters, updateFilter, setPage, page,
    rows: data?.data ?? [],
    total: data?.total ?? 0,
    pages: data?.total_pages ?? 1,
  }
}
