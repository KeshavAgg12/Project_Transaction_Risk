import './PipelineFlow.css'
import PipelineNode from './PipelineNode.jsx'

export default function PipelineFlow({ nodes, selectedIndex, onSelect }) {
  return (
    <div className="flow">
      {nodes.map((node, index) => (
        <div key={node.name}>
          {index > 0 && <div className="conn" aria-hidden />}
          <PipelineNode node={node} selected={index === selectedIndex} onSelect={() => onSelect(index)} />
        </div>
      ))}
    </div>
  )
}
