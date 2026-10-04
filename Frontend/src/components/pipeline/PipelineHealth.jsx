import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import Card from '../ui/Card.jsx'
import { AXIS_STYLE } from '../../utils/chartTheme.js'

export default function PipelineHealth({ nodes }) {
  const totalLatency = nodes.reduce((sum, node) => sum + node.latency, 0)
  return (
    <Card title="Pipeline health">
      <p className="sub tight">End-to-end latency {totalLatency} ms · Throughput 1.23M/day · Queue depth 142</p>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={nodes}>
          <CartesianGrid stroke="var(--color-border)" vertical={false} />
          <XAxis dataKey="name" hide />
          <YAxis {...AXIS_STYLE} unit="ms" />
          <Tooltip />
          <Bar dataKey="latency" fill="#2563eb" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  )
}
