import './Pipeline.css'
import { useState } from 'react'
import ErrorState from '../components/ui/ErrorState.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import Skeleton from '../components/ui/Skeleton.jsx'
import NodeDetails from '../components/pipeline/NodeDetails.jsx'
import PipelineFlow from '../components/pipeline/PipelineFlow.jsx'
import PipelineHealth from '../components/pipeline/PipelineHealth.jsx'
import { useAsync } from '../hooks/useAsync.js'
import { getPipelineStatus } from '../services/pipelineService.js'

export default function Pipeline() {
  const { data: nodes, loading, error } = useAsync(getPipelineStatus)
  const [selectedIndex, setSelectedIndex] = useState(3)

  return (
    <>
      <PageHeader title="Pipeline" subtitle="Live view of each stage a transaction passes through (demo data)." />
      {loading && <Skeleton rows={8} />}
      {error && <ErrorState message={error} />}
      {nodes && (
        <div className="grid two">
          <PipelineFlow nodes={nodes} selectedIndex={selectedIndex} onSelect={setSelectedIndex} />
          <div className="stack">
            <NodeDetails node={nodes[selectedIndex]} />
            <PipelineHealth nodes={nodes} />
          </div>
        </div>
      )}
    </>
  )
}
