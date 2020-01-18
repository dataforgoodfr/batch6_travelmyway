import React from 'react'
import SearchContainer from './search/SearchContainer'
import Header from './components/Header'

const Home = ({ setResults }) => {
  return (
    <main className="main-home">
      <Header />
      <div className="main-home_title">
        <h2>Faites le meilleur choix.</h2>
        <h3>
          Trouvez le trajet qui vous ressemble : porte-à-porte, au meilleur prix et respectueux de
          l'environnement
        </h3>
      </div>
      <SearchContainer setResults={setResults} />
    </main>
  )
}

export default Home
