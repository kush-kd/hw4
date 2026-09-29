import { Link } from 'react-router-dom'
import './NotFound.css'

export default function NotFound() {
  return (
    <div className="container not-found-page">
      <p className="eyebrow">404</p>
      <h1>We couldn't find that page.</h1>
      <p>
        The link might be old, or the address might have a typo. Here are a couple of places to
        pick back up:
      </p>
      <div className="not-found-actions">
        <Link to="/" className="btn btn-primary">
          Back to Home
        </Link>
        <Link to="/products" className="btn btn-secondary">
          Browse products
        </Link>
      </div>
    </div>
  )
}
