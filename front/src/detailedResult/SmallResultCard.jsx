import React from 'react'
import { Grid } from 'semantic-ui-react'
import { getTimeFromDate, getDurationFromSeconds, journeyType } from '../journey.utils'

const SmallResultCard = ({ result }) => {
  const departureHour = getTimeFromDate(result.departure_date)
  const arrivalHour = getTimeFromDate(result.arrival_date)
  const totalDuration = getDurationFromSeconds(result.total_duration)
  const renderStep = step => {
    return <i className="material-icons">{journeyType[step]}</i>
  }
  return (
    <div className="small-result-card">
      <div className="header flex align-center">
        {renderStep(result.category[0])}
        <p>Voir ></p>
      </div>
      <div className="content">
        <Grid stackable>
          <Grid.Row>
            <Grid.Column floated="left" width={6}>
              <div className="flex space-between">
                <div>
                  <p className="text-large">{departureHour}</p>
                  <p className="text-info">départ</p>
                </div>
                <div>
                  <p className="text-large">{arrivalHour}</p>
                  <p className="text-info">arrivée</p>
                </div>
              </div>
            </Grid.Column>
            <Grid.Column floated="right" width={8}>
              <div className="flex space-between">
                <div>
                  <p className="text-large">{totalDuration}</p>
                  <p className="text-info no-wrap">durée totale</p>
                </div>
                <div>
                  <p className="text-large">{result.total_price_EUR} €</p>
                  <p className="text-info no-wrap">prix total</p>
                </div>
              </div>
            </Grid.Column>
          </Grid.Row>
        </Grid>
      </div>
    </div>
  )
}

export default SmallResultCard
