import { Link } from 'react-router-dom'
import Crest from './Crest'
import './Footer.css'

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="container footer-inner">
        <div className="footer-brand">
          <Crest size={34} />
          <div>
            <p className="footer-title">Campus Customs</p>
            <p className="footer-tagline">Yale gear, straight from New Haven.</p>
          </div>
        </div>

        <div className="footer-col">
          <h4>Shop</h4>
          <Link to="/products">All products</Link>
          <Link to="/about">About us</Link>
        </div>

        <div className="footer-col">
          <h4>Account</h4>
          <Link to="/login">Log in</Link>
          <Link to="/create-account">Create account</Link>
        </div>

        <div className="footer-col">
          <h4>Visit</h4>
          <p>57 Broadway</p>
          <p>New Haven, CT 06511</p>
        </div>
      </div>
      <div className="footer-bottom">
        <div className="container">© {new Date().getFullYear()} Campus Customs. Made for Yale, by Yale.</div>
      </div>
    </footer>
  )
}
