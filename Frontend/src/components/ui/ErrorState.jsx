export default function ErrorState({ message }) {
  return (
    <div className="card" role="alert">
      <b>Something went wrong</b>
      <p className="sub">{message}. Check the service layer and retry.</p>
    </div>
  )
}
