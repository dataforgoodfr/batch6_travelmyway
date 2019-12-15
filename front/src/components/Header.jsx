import React from 'react'
import { Link } from 'react-router-dom'

function Header() {
  return (
    <nav className="top-navbar">
      <div className="top-navbar_logo">
        <Link to="/" className="bold">
          travel my way
        </Link>
      </div>

      <div className="top-navbar_connexion">
        <a href="#">Mon compte</a>
      </div>
    </nav>
  )
}

export default Header
