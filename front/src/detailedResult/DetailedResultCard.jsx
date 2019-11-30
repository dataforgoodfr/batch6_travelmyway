import React from 'react'
import { Grid, Button } from 'semantic-ui-react'
import { getDurationFromSeconds, getTimeFromDate } from '../journey.utils'

const DetailedResultCard = ({ result }) => {
  const departureHour = getTimeFromDate(result.departure_date)
  const arrivalHour = getTimeFromDate(result.arrival_date)
  const totalPrice = `${result.total_price_EUR} €`
  const totalDuration = getDurationFromSeconds(result.total_duration)
  return (
    <div className="card">
      <Grid>
        <Grid.Row>
          <Grid.Column floated="left" width={5}>
            <div className="flex space-between">
              <div>
                <p className="text-large">{departureHour}</p>
                <p className="text-info">départ</p>
              </div>
              <div>
                <p className="text-large">{arrivalHour}</p>
                <p className="text-info">arrivée</p>
              </div>
              <div>
                <p className="text-large">{totalDuration}</p>
                <p className="text-info">durée totale</p>
              </div>
            </div>
          </Grid.Column>
          <Grid.Column width={6} floated="right">
            <div className="flex space-between">
              <div>
                <p className="text-large">{totalPrice}</p>
                <p className="text-info">tarif total</p>
              </div>
              <div>
                <Button>Aller sur trainline.fr</Button>
                <p className="text-info">Pour réserver le billet de train</p>
              </div>
            </div>
          </Grid.Column>
        </Grid.Row>
      </Grid>
    </div>
  )
}

export default DetailedResultCard
