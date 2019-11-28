import React from 'react'
import moment from 'moment'
import { Grid } from 'semantic-ui-react'

const ResultCard = ({ result }) => {
  moment().locale('fr')
  const departureHour = moment(result.departure_date).format('HH:mm')
  const arrivalHour = moment(result.arrival_date).format('HH:mm')
  const totalPrice = `${result.total_price_EUR} €`
  const totalDuration = moment.utc(result.total_duration * 1000).format('HH:mm')
  return (
    <div className="result-card">
      <Grid>
        <Grid.Row>
          <Grid.Column width={4}>
            <div className="hour">
              <p>{departureHour}</p>
              <p>départ</p>
            </div>
          </Grid.Column>
          <Grid.Column width={4}>
            <div className="hour">
              <p>{arrivalHour}</p>
              <p>arrivée</p>
            </div>
          </Grid.Column>
          <Grid.Column width={4}>
            <div className="hour">
              <p>{totalDuration}</p>
              <p>durée totale</p>
            </div>
          </Grid.Column>
          <Grid.Column width={4}>
            <div className="hour">
              <p>{totalPrice}</p>
              <p>prix total</p>
            </div>
          </Grid.Column>
        </Grid.Row>
      </Grid>
    </div>
  )
}

export default ResultCard
