import './Pagination.css'
import Button from '../ui/Button.jsx'

export default function Pagination({ total, page, pages, onChange }) {
  return (
    <div className="pager">
      <span>{total} results</span>
      <span>
        <Button disabled={page === 1} onClick={() => onChange(page - 1)}>Previous</Button>
        {' '}Page {page} of {pages}{' '}
        <Button disabled={page === pages} onClick={() => onChange(page + 1)}>Next</Button>
      </span>
    </div>
  )
}
