const TIME_ZONE = 'Asia/Kolkata'
const money = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
const number = new Intl.NumberFormat('en-IN')

export const formatMoney = (value) => money.format(value)
export const formatNumber = (value) => number.format(value)
export const formatDate = (value) =>
  new Date(value).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short', timeZone: TIME_ZONE })
