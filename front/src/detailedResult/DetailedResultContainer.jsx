import React from 'react'
import { Link } from 'react-router-dom'
import { Grid } from 'semantic-ui-react'
import DetailedResultCard from './DetailedResultCard'
import SmallResultCard from './SmallResultCard'
import EcologyCard from './EcologyCard'
import StepsCard from './StepsCard'
import Header from '../components/Header'
import SearchBarRecap from './SearchBarRecap'
import { getCO2InKg } from '../journey.utils'


const DetailedResultContainer = ({ selectedJourney, journeys }) => {
  const totalCO2InKg = getCO2InKg(selectedJourney.total_gCO2)
  return (
    <div className="page-detailed-results">
      <Header />
      <SearchBarRecap />
      <main className="content-wrapper">
        <Grid stackable>
          <Grid.Row>
            <Grid.Column>
              <DetailedResultCard selectedJourney={selectedJourney} />
            </Grid.Column>
          </Grid.Row>
          <Grid.Row>
            <Grid.Column width={8}>
              <StepsCard steps={selectedJourney.journey_steps} />
            </Grid.Column>
            <Grid.Column width={8}>
              <h3 className="ecology">{totalCO2InKg} de CO2 émis</h3>
              <EcologyCard />
              <p>Les autres trajets écologiques</p>
              <br />
              {journeys.map(item => (
                <Link key={item.id} to={`/results/${item.id}`}>
                  <SmallResultCard result={item} />
                </Link>
              ))}
              <Link to="/results" className="center">
                Voir toutes les options >
              </Link>
            </Grid.Column>
          </Grid.Row>
        </Grid>
      </main>
    </div>
  )
}

export default DetailedResultContainer
