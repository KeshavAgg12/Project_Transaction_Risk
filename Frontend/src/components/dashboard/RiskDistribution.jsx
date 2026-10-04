import { useMemo, useState } from 'react'
import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import Card from '../ui/Card.jsx'
import Segmented from '../ui/Segmented.jsx'
import { AXIS_STYLE, CHART_COLORS } from '../../utils/chartTheme.js'

// LOW is ~98% of rows and would flatten everything else, so the chart shows only the risky levels.
const LEVELS = ['medium', 'high', 'critical']

const toPercentages = (day) => {
  const total = day.low + day.medium + day.high + day.critical
  const next = { ...day }
  LEVELS.forEach((level) => { next[level] = total ? +((day[level] / total) * 100).toFixed(2) : 0 })
  return next
}

export default function RiskDistribution({ data }) {
  const [mode, setMode] = useState('Volume')
  const chartData = useMemo(() => (mode === 'Volume' ? data : data.map(toPercentages)), [data, mode])

  return (
    <Card title="Elevated risk by day" actions={<Segmented label="Chart mode" options={['Volume', 'Percentage']} value={mode} onChange={setMode} />}>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={chartData}>
          <CartesianGrid stroke="var(--color-border)" vertical={false} />
          <XAxis dataKey="date" {...AXIS_STYLE} />
          <YAxis {...AXIS_STYLE} />
          <Tooltip />
          <Legend />
          {LEVELS.map((level) => (
            <Area key={level} dataKey={level} stackId="1" stroke={CHART_COLORS[level]} fill={CHART_COLORS[level]} fillOpacity={0.25} />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  )
}
