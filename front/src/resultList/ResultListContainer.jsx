import React from 'react'
import { Grid } from 'semantic-ui-react'
import ResultCard from './ResultCard'
import Header from '../components/Header'
import SearchContainer from '../search/SearchContainer'
import fakeJourney from '../../fakeJourney'

const ResultListContainer = () => {
  const results = [fakeJourney]
  return (
    <div className="page-results">
      <Header />
      <SearchContainer />
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
                  <ResultCard result={result} key={result.id} />
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
