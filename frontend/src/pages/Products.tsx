import { useEffect, useMemo, useState } from 'react'
import { fetchProducts } from '../api'
import ProductCard from '../components/ProductCard'
import type { ProductSummary } from '../types'
import './Products.css'

export default function Products() {
  const [products, setProducts] = useState<ProductSummary[]>([])
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [query, setQuery] = useState('')
  const [garmentType, setGarmentType] = useState('all')

  useEffect(() => {
    let cancelled = false
    fetchProducts()
      .then((data) => {
        if (!cancelled) {
          setProducts(data)
          setStatus('ready')
        }
      })
      .catch(() => {
        if (!cancelled) setStatus('error')
      })
    return () => {
      cancelled = true
    }
  }, [])

  const garmentTypes = useMemo(
    () => ['all', ...Array.from(new Set(products.map((p) => p.garment_type))).sort()],
    [products],
  )

  const filtered = useMemo(() => {
    return products.filter((product) => {
      const matchesType = garmentType === 'all' || product.garment_type === garmentType
      const matchesQuery =
        query.trim().length === 0 ||
        product.name.toLowerCase().includes(query.toLowerCase()) ||
        product.description.toLowerCase().includes(query.toLowerCase())
      return matchesType && matchesQuery
    })
  }, [products, query, garmentType])

  return (
    <div className="container products-page">
      <div className="products-header">
        <div>
          <p className="eyebrow">The full collection</p>
          <h1>All Products</h1>
        </div>
        <div className="products-controls">
          <input
            type="search"
            placeholder="Search products…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="products-search"
          />
          <select value={garmentType} onChange={(event) => setGarmentType(event.target.value)} className="products-filter">
            {garmentTypes.map((type) => (
              <option key={type} value={type}>
                {type === 'all' ? 'All types' : type}
              </option>
            ))}
          </select>
        </div>
      </div>

      {status === 'loading' && (
        <div className="products-grid">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="product-skeleton" />
          ))}
        </div>
      )}

      {status === 'error' && (
        <p className="products-error">
          Couldn't load products. Is the backend running at <code>http://localhost:8000</code>?
        </p>
      )}

      {status === 'ready' && filtered.length === 0 && (
        <p className="products-empty">No products match "{query}".</p>
      )}

      {status === 'ready' && filtered.length > 0 && (
        <div className="products-grid">
          {filtered.map((product) => (
            <ProductCard key={product.product_id} product={product} />
          ))}
        </div>
      )}
    </div>
  )
}
