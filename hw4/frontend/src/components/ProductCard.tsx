import { Link } from 'react-router-dom'
import type { ProductSummary } from '../types'
import { swatchStyle } from '../utils/colorSwatch'
import './ProductCard.css'

const LOW_STOCK_THRESHOLD = 20

export default function ProductCard({ product }: { product: ProductSummary }) {
  const isLowStock = product.total_stock > 0 && product.total_stock <= LOW_STOCK_THRESHOLD

  return (
    <Link to={`/products/${product.product_id}`} className="product-card">
      <div className="product-card-image">
        {isLowStock && <span className="product-card-badge">Low stock — {product.total_stock} left</span>}
        <img src={product.image_url} alt={product.name} loading="lazy" />
      </div>
      <div className="product-card-body">
        <p className="product-card-type">{product.garment_type}</p>
        <h3>{product.name}</h3>
        <p className="product-card-desc">{product.description}</p>
        <div className="product-card-footer">
          <p className="product-card-price">${product.price.toFixed(2)}</p>
          {product.colors.length > 0 && (
            <div className="product-card-swatches" aria-hidden="true">
              {product.colors.slice(0, 4).map((color) => (
                <span
                  key={color}
                  className="swatch-dot"
                  style={{ background: swatchStyle(color) }}
                  title={color}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}
