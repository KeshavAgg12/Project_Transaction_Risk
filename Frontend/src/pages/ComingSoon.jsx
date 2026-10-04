import Button from '../components/ui/Button.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'

export default function ComingSoon({ title }) {
  return (
    <>
      <PageHeader title={title} subtitle="This page is not built yet. Its route and nav item are ready." />
      <Button to="/" variant="primary">Go to overview</Button>
    </>
  )
}
