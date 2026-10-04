import Button from '../components/ui/Button.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'

export default function NotFound() {
  return (
    <>
      <PageHeader title="Page not found" subtitle="This address does not exist." />
      <Button to="/" variant="primary">Go to overview</Button>
    </>
  )
}
