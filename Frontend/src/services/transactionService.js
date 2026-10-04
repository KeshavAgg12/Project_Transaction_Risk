import { apiGet } from './apiClient.js'

export const getTransactions = (params) => apiGet('/transactions', params)
export const getTransactionById = (id) => apiGet(`/transactions/${encodeURIComponent(id)}`)
