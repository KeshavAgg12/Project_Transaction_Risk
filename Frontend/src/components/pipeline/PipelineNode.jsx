import './PipelineNode.css'
import { formatNumber } from '../../utils/formatters.js'

export default function PipelineNode({ node, selected, onSelect }) {
  return (
    <button className={`node ${node.status} ${selected ? 'sel' : ''}`} onClick={onSelect} aria-label={`${node.name}, ${node.status}`}>
      <div className="row">
        <span className="node-title">{node.name}</span>
        <span className={`badge ${node.status}`}>{node.status}</span>
      </div>
      <small>Processed {formatNumber(node.processed)} · Latency {node.latency}ms · Errors {node.errors}%</small>
    </button>
  )
}
