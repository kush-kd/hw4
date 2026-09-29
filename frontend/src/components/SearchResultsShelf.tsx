import ProductCard from './ProductCard'
import { useSearchResults } from '../context/SearchResultsContext'
import './SearchResultsShelf.css'

export default function SearchResultsShelf() {
  const { results, clearResults } = useSearchResults()

  if (!results) return null

  return (
    <div className="search-shelf">
      <div className="container search-shelf-inner">
        <div className="search-shelf-header">
          <p>
            <span className="search-shelf-icon">💬</span> From your chat — matches for{' '}
            <strong>&ldquo;{results.query}&rdquo;</strong> ({results.products.length})
          </p>
          <button type="button" onClick={clearResults} aria-label="Dismiss search results">
            ×
          </button>
        </div>
        <div className="search-shelf-track">
          {results.products.map((product) => (
            <div className="search-shelf-item" key={product.product_id}>
              <ProductCard product={product} />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
