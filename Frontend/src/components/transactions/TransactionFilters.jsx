import './TransactionFilters.css'
import Input from '../ui/Input.jsx'
import Select from '../ui/Select.jsx'
import { DECISIONS, PAYMENT_METHODS, RISK_LEVELS } from '../../utils/riskHelpers.js'

export default function TransactionFilters({ filters, onChange }) {
  return (
    <div className="filters">
      <Input label="Search transaction or customer ID" value={filters.search} onChange={(e) => onChange('search', e.target.value)} />
      <Select label="Risk" value={filters.level} options={RISK_LEVELS} onChange={(v) => onChange('level', v)} />
      <Select label="Decision" value={filters.decision} options={DECISIONS} onChange={(v) => onChange('decision', v)} />
      <Select label="Payment method" value={filters.payment_method} options={PAYMENT_METHODS} onChange={(v) => onChange('payment_method', v)} />
      <select className="input box" aria-label="Sort" value={filters.sort} onChange={(e) => onChange('sort', e.target.value)}>
        <option value="time">Sort: newest</option>
        <option value="risk">Sort: highest risk</option>
        <option value="amount">Sort: largest amount</option>
      </select>
    </div>
  )
}
