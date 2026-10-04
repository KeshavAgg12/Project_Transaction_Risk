import './Skeleton.css'
export default function Skeleton({ rows = 5 }) {
  return (
    <div role="status" aria-label="Loading">
      {Array.from({ length: rows }, (_, index) => <div key={index} className="skel" />)}
    </div>
  )
}
