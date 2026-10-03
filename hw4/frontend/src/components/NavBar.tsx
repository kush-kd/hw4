import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Crest from './Crest'
import './NavBar.css'

const links = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  // Problem 9 (front-end usability improvement): see NavBar.css's mobile
  // media query comment and output/usability.md for the bug this fixes —
  // "Log in" (and "Log out") were completely unreachable on a phone-width
  // screen before this.
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  function closeMenu() {
    setIsMenuOpen(false)
  }

  function handleLogout() {
    logout()
    closeMenu()
    navigate('/')
  }

  return (
    <header className="navbar">
      <div className="container navbar-inner">
        <NavLink to="/" className="navbar-brand" end onClick={closeMenu}>
          <Crest size={32} />
          <span className="navbar-wordmark">
            CAMPUS <span>CUSTOMS</span>
          </span>
        </NavLink>
        <nav className="navbar-links">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => (isActive ? 'navbar-link active' : 'navbar-link')}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="navbar-auth">
          {user ? (
            <>
              <span className="navbar-greeting">Hi, {user.first_name}</span>
              <button type="button" className="navbar-auth-link navbar-logout" onClick={handleLogout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className={({ isActive }) => `navbar-auth-link ${isActive ? 'active' : ''}`}>
                Log in
              </NavLink>
              <NavLink
                to="/create-account"
                className={({ isActive }) => `navbar-auth-link navbar-auth-cta ${isActive ? 'active' : ''}`}
              >
                Create account
              </NavLink>
            </>
          )}
        </div>
        <button
          type="button"
          className={`navbar-hamburger ${isMenuOpen ? 'open' : ''}`}
          aria-label={isMenuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={isMenuOpen}
          onClick={() => setIsMenuOpen((open) => !open)}
        >
          <span />
          <span />
          <span />
        </button>
      </div>

      {isMenuOpen && (
        <nav className="navbar-mobile-menu">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => `navbar-mobile-link ${isActive ? 'active' : ''}`}
              onClick={closeMenu}
            >
              {link.label}
            </NavLink>
          ))}
          <div className="navbar-mobile-divider" />
          {user ? (
            <>
              <span className="navbar-mobile-greeting">Signed in as {user.first_name}</span>
              <button type="button" className="navbar-mobile-link" onClick={handleLogout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className="navbar-mobile-link" onClick={closeMenu}>
                Log in
              </NavLink>
              <NavLink to="/create-account" className="navbar-mobile-link navbar-mobile-cta" onClick={closeMenu}>
                Create account
              </NavLink>
            </>
          )}
        </nav>
      )}
    </header>
  )
}
