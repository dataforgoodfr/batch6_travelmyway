import React from 'react'
import Header from '../components/Header'
import { Link } from 'react-router-dom'
import DetailedResultCard from './DetailedResultCard'
import ResultCard from '../resultList/ResultCard'
import EcologyCard from './EcologyCard'
import StepsCard from './StepsCard'
import SearchRecap from '../search/SearchRecap'
import { Grid } from 'semantic-ui-react'
import { getCO2InKg } from '../journey.utils'

const DetailedResult = ({ result, results }) => {
  const totalCO2InKg = getCO2InKg(result.total_gCO2)
  return (
    <div className="page-results">
      <Header />
      <SearchRecap></SearchRecap>
      <main className="content-wrapper">
        <Grid>
          <Grid.Row>
            <Grid.Column>
              <DetailedResultCard result={result} />
            </Grid.Column>
          </Grid.Row>
          <Grid.Row>
            <Grid.Column width={8}>
              <StepsCard steps={result.journey_steps}></StepsCard>
            </Grid.Column>
            <Grid.Column width={8}>
              <h3 className="ecology">{totalCO2InKg} de CO2 émis</h3>
              <EcologyCard></EcologyCard>
              <p>Les autres trajets écologiques</p>
              {results.map(result => (
                <Link key={result.id} to={`/results/${result.id}`}>
                  <ResultCard result={result} />
                </Link>
              ))}
              <Link to="/results">Voir toutes les options ></Link>
            </Grid.Column>
          </Grid.Row>
        </Grid>
      </main>
    </div>
  )
}

export default DetailedResult
