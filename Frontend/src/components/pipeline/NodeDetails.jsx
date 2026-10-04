import '../ui/DescriptionList.css'
import Card from '../ui/Card.jsx'
import { formatNumber } from '../../utils/formatters.js'

export default function NodeDetails({ node }) {
  return (
    <Card title={node.name}>
      <dl className="dl">
        <dt>Status</dt><dd className={node.status}>{node.status}</dd>
        <dt>Processed</dt><dd>{formatNumber(node.processed)}</dd>
        <dt>Avg latency</dt><dd>{node.latency} ms</dd>
        <dt>Error rate</dt><dd>{node.errors}%</dd>
      </dl>
    </Card>
  )
}
