import React from 'react'
import { Grid, Button } from 'semantic-ui-react'
import { getDurationFromSeconds, getTimeFromDate } from '../journey.utils'

const DetailedResultCard = ({ selectedJourney }) => {
  const departureHour = getTimeFromDate(selectedJourney.departure_date)
  const arrivalHour = getTimeFromDate(selectedJourney.arrival_date)
  const totalPrice = `${selectedJourney.total_price_EUR} €`
  const totalDuration = getDurationFromSeconds(selectedJourney.total_duration)
  return (
    <div className="detailed-result-card">
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
          <Grid.Column width={8} floated="right">
            <div className="flex space-between">
              <div>
                <p className="text-large">{totalPrice}</p>
                <p className="text-info">prix total</p>
              </div>
              <div>
                <a className="button primary" href="https://www.trainline.fr/" target="_blank">
                  Aller sur trainline.fr
                </a>
                <p className="text-info center">Pour réserver le billet de train</p>
              </div>
            </div>
          </Grid.Column>
        </Grid.Row>
      </Grid>
    </div>
  )
}

export default DetailedResultCard
