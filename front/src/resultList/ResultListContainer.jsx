import React from 'react'
import { Grid } from 'semantic-ui-react'
import { Link } from 'react-router-dom'
import ResultCard from './ResultCard'
import Header from '../components/Header'
import SearchContainer from '../search/SearchContainer'

const ResultListContainer = ({ results, setResults }) => {
  return (
    <div className="page-results">
      <Header />
      <SearchContainer setResults={setResults} />
      <main className="content-wrapper">
        <Grid>
          <Grid.Row>
            <Grid.Column width={4}>
              <div className="column">Trier par</div>
            </Grid.Column>
            <Grid.Column width={12}>
              <div className="column">
                <h2>Travel my Way vous recommande</h2>
                {results.map(result => (
                  <Link key={result.id} to={`/results/${result.id}`}>
                    <ResultCard result={result} />
                  </Link>
                ))}
              </div>
            </Grid.Column>
          </Grid.Row>
        </Grid>
      </main>
    </div>
  )
}

export default ResultListContainer
