import React from 'react'
import SearchContainer from './search/SearchContainer'

const Home = () => {
  return (
    <main className="main-home">
      <div className="main-home_title">
        <h2>Faites le meilleur choix.</h2>
      </div>
      <SearchContainer />
    </main>
  )
}

export default Home
