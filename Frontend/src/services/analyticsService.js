import { apiGet } from './apiClient.js'

export const getOverview = (range) => apiGet('/overview', { range })
