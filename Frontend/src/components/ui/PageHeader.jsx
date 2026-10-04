import './PageHeader.css'
export default function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="page-header">
      <div>
        <h1>{title}</h1>
        <p className="sub">{subtitle}</p>
      </div>
      {actions}
    </div>
  )
}
