import React from 'react'
import { Link } from 'react-router-dom'

const SearchBarRecap = selectedJourney => {
  console.log('journey', selectedJourney)
  return (
    <div className="search-recap">
      <p>
        <Link to="/results" className="text-large">
          ‹
        </Link>
        <span className="text-info">|</span>
        <span className="text-info">De</span> 9 Rue d'Alexandrie, Paris 02
        <span className="text-info">à </span> Helenenstraße 14, 50667 Köln, Allemagne
        <span className="text-info">le</span>mer. 17 oct. 6h
        <span>
          <Link className="text-info">✎ modifier</Link>
        </span>
      </p>
    </div>
  )
}

export default SearchBarRecap
