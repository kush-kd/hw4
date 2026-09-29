import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts } from '../api'
import Crest from '../components/Crest'
import ProductCard from '../components/ProductCard'
import Reveal from '../components/Reveal'
import StatCounter from '../components/StatCounter'
import type { ProductSummary } from '../types'
import './Home.css'

const STATS = [
  { value: 100, suffix: '+', label: 'styles in stock' },
  { value: 11, suffix: '', label: 'residential colleges repped' },
  { value: 6, suffix: '', label: 'sizes, XS–XXL' },
]

// Curated, not "first 3 alphabetically": about a quarter of the catalogue's
// photos have a white/near-white backdrop and the rest are shot on black —
// picking arbitrarily means the hero collage sometimes mixes the two and
// looks like a mistake rather than a design choice. These three are checked
// black-backdrop shots spanning hoodie/crewneck/tee, so the collage reads as
// one consistent, intentional photo treatment. See design.md.
const HERO_PRODUCT_IDS = ['basic-hoodie-big-yale', 'baseball-left-chest-crewneck', 'boola-boola-t-shirt']

export default function Home() {
  const [products, setProducts] = useState<ProductSummary[]>([])

  useEffect(() => {
    let cancelled = false
    fetchProducts().then((data) => {
      if (!cancelled) setProducts(data)
    })
    return () => {
      cancelled = true
    }
  }, [])

  const curatedHero = HERO_PRODUCT_IDS.map((id) => products.find((p) => p.product_id === id)).filter(
    (p): p is ProductSummary => Boolean(p),
  )
  const heroImages = curatedHero.length === HERO_PRODUCT_IDS.length ? curatedHero : products.slice(0, 3)
  const featuredIds = new Set(heroImages.map((p) => p.product_id))
  const featured = products.filter((p) => !featuredIds.has(p.product_id)).slice(0, 4)

  return (
    <div className="home">
      <section className="hero">
        <Crest size={340} className="hero-watermark" />
        <div className="container hero-inner">
          <div className="hero-copy">
            <p className="eyebrow">New Haven, Connecticut</p>
            <h1>Gear up in Yale Blue.</h1>
            <p className="hero-sub">
              Campus Customs is the go-to shop for Yale students, alumni, and families who want
              hoodies, tees, and college-crest gear that actually feels like campus. Every piece
              you see here is pulled straight from our real stockroom — if it's on the page, we
              can tell you exactly how many are left.
            </p>
            <div className="hero-actions">
              <Link to="/products" className="btn btn-primary">
                Shop the collection
              </Link>
              <Link to="/about" className="btn btn-secondary">
                Our story
              </Link>
            </div>
          </div>
          <div className="hero-collage">
            {heroImages.map((product, index) => (
              <div key={product.product_id} className={`hero-collage-item item-${index}`}>
                <img src={product.image_url} alt={product.name} />
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="stats-strip">
        <div className="container stats-inner">
          {STATS.map((stat) => (
            <StatCounter key={stat.label} value={stat.value} suffix={stat.suffix} label={stat.label} />
          ))}
        </div>
      </section>

      <section className="container home-highlights">
        <Reveal>
          <div className="highlight-card">
            <Crest size={26} className="highlight-icon" />
            <h3>Residential college pride</h3>
            <p>Crewnecks and tees repping every one of Yale's residential colleges, from Berkeley to Trumbull.</p>
          </div>
        </Reveal>
        <Reveal delay={100}>
          <div className="highlight-card">
            <svg className="highlight-icon" width="26" height="26" viewBox="0 0 26 26" fill="none" aria-hidden="true">
              <circle cx="13" cy="13" r="11" stroke="var(--gold)" strokeWidth="1.6" />
              <path d="M8 13.5 L11.5 17 L18.5 9.5" stroke="var(--gold)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <h3>Real-time stock</h3>
            <p>Our chatbot checks the same database our store runs on, so sizing answers are always honest.</p>
          </div>
        </Reveal>
        <Reveal delay={200}>
          <div className="highlight-card">
            <svg className="highlight-icon" width="26" height="26" viewBox="0 0 26 26" fill="none" aria-hidden="true">
              <path
                d="M4 4 V22 M4 4 L20 8 L4 13"
                stroke="var(--gold)"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <h3>Built for game day</h3>
            <p>Hoodies, fleeces, and tailgate layers ready for a New Haven fall on the Bowl sidelines.</p>
          </div>
        </Reveal>
      </section>

      {featured.length > 0 && (
        <section className="container featured-section">
          <Reveal>
            <div className="featured-header">
              <div>
                <p className="eyebrow">Fresh off the shelf</p>
                <h2>Featured picks</h2>
              </div>
              <Link to="/products" className="featured-link">
                View all products →
              </Link>
            </div>
          </Reveal>
          <div className="featured-grid">
            {featured.map((product, index) => (
              <Reveal key={product.product_id} delay={index * 80}>
                <ProductCard product={product} />
              </Reveal>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
