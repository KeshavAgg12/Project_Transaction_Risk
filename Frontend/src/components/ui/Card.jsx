import './Card.css'
export default function Card({ title, actions, spaced = false, children }) {
  return (
    <section className={`card ${spaced ? 'spaced' : ''}`}>
      {(title || actions) && (
        <div className="card-head">
          {title && <h3>{title}</h3>}
          {actions}
        </div>
      )}
      {children}
    </section>
  )
}
