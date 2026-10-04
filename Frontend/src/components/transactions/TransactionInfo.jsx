import '../ui/DescriptionList.css'
import { Fragment } from 'react'
import Card from '../ui/Card.jsx'
import { formatDate, formatMoney } from '../../utils/formatters.js'

export default function TransactionInfo({ transaction: t }) {
  const fields = [
    ['Transaction ID', t.transaction_id], ['Amount', formatMoney(t.amount)], ['Currency', t.currency],
    ['Timestamp', formatDate(t.timestamp)], ['Merchant category', t.merchant_category], ['Payment method', t.payment_method],
    ['Customer ID', t.customer_id], ['Distance from home', `${Math.round(t.distance_from_home_km)} km`],
    ['Transactions last hour', t.transactions_last_hour], ['Hour of day', t.hour_of_day], ['Source', t.source],
  ]
  return (
    <Card title="Transaction information">
      <dl className="dl">
        {fields.map(([label, value]) => <Fragment key={label}><dt>{label}</dt><dd>{value}</dd></Fragment>)}
      </dl>
    </Card>
  )
}
