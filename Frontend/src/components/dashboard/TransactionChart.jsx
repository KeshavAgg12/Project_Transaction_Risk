import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import Card from '../ui/Card.jsx'
import { AXIS_STYLE, CHART_COLORS } from '../../utils/chartTheme.js'

const SERIES = ['approved', 'review', 'blocked']

export default function TransactionChart({ data }) {
  return (
    <Card title="Transaction Activity">
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid stroke="var(--color-border)" vertical={false} />
          <XAxis dataKey="date" {...AXIS_STYLE} />
          <YAxis {...AXIS_STYLE} />
          <Tooltip />
          <Legend />
          {SERIES.map((key) => <Line key={key} dataKey={key} stroke={CHART_COLORS[key]} dot={false} strokeWidth={2} />)}
        </LineChart>
      </ResponsiveContainer>
    </Card>
  )
}
