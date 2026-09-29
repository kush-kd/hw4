import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct } from '../api'
import type { ProductDetail as ProductDetailType } from '../types'
import './ProductDetail.css'

export default function ProductDetail() {
  const { productId } = useParams<{ productId: string }>()
  const [product, setProduct] = useState<ProductDetailType | null>(null)
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')

  useEffect(() => {
    if (!productId) return
    let cancelled = false
    setStatus('loading')
    fetchProduct(productId)
      .then((data) => {
        if (!cancelled) {
          setProduct(data)
          setStatus('ready')
        }
      })
      .catch(() => {
        if (!cancelled) setStatus('error')
      })
    return () => {
      cancelled = true
    }
  }, [productId])

  if (status === 'loading') {
    return (
      <div className="container product-detail-page">
        <div className="product-detail-grid">
          <div className="product-skeleton-image" />
          <div className="product-skeleton-info">
            <div className="skeleton-line" style={{ width: '70%', height: 32 }} />
            <div className="skeleton-line" style={{ width: '30%', height: 24 }} />
            <div className="skeleton-line" />
            <div className="skeleton-line" />
          </div>
        </div>
      </div>
    )
  }

  if (status === 'error' || !product) {
    return (
      <div className="container product-detail-page">
        <p className="products-error">Couldn't find that product.</p>
        <Link to="/products">Back to all products</Link>
      </div>
    )
  }

  return (
    <div className="container product-detail-page">
      <nav className="breadcrumb">
        <Link to="/products">Products</Link>
        <span>/</span>
        <span>{product.name}</span>
      </nav>
      <div className="product-detail-grid">
        <div className="product-detail-image">
          <img src={product.image_url} alt={product.name} />
        </div>
        <div className="product-detail-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="product-detail-price">${product.price.toFixed(2)}</p>
          <p className="product-detail-desc">{product.description}</p>

          <h3>Colors</h3>
          <div className="swatch-row">
            {product.colors.map((color) => (
              <span key={color} className="swatch-pill">
                {color}
              </span>
            ))}
          </div>

          <h3>Sizes &amp; stock</h3>
          <ul className="size-list">
            {product.sizes.map((s) => (
              <li key={s.size} className={s.quantity === 0 ? 'size-out' : 'size-in'}>
                <span className="size-name">{s.size}</span>
                <span className="size-qty">{s.quantity === 0 ? 'Out of stock' : `${s.quantity} left`}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
