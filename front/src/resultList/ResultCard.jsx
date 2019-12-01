import React from 'react'
import { getTimeFromDate, getDurationFromSeconds } from '../journey.utils'

const renderStep = step => {
  const journeyType = {
    Walking: <i className="material-icons">directions_walking</i>,
    Coach: <i className="material-icons">directions_bus</i>,
    ratp: <i className="material-icons">subway</i>,
    tisséo: <i className="material-icons">face</i>,
    Waiting: <i className="material-icons">airline_seat_recline_normal</i>
  }
  return (
    <div key={step.id} className="step">
      {journeyType[step.type]}
      <p className="text-info">{getDurationFromSeconds(step.duration_s)}</p>
    </div>
  )
}

const ResultCard = ({ result }) => {
  const departureHour = getTimeFromDate(result.departure_date)
  const arrivalHour = getTimeFromDate(result.arrival_date)
  const totalDuration = getDurationFromSeconds(result.total_duration)

  return (
    <div className="result-card">
      <div className="space-between flex flex-row">
        <div className="inline-flex">
          <div className="info-wrapper">
            <p className="text-large">{departureHour}</p>
            <p className="text-info">départ</p>
          </div>
          <div className="info-wrapper">
            <p className="text-large">{arrivalHour}</p>
            <p className="text-info">arrivée</p>
          </div>
        </div>
        <div className="inline-flex right">
          <div className="info-wrapper">
            <p className="text-large">{totalDuration}</p>
            <p className="text-info">durée totale</p>
          </div>
          <div className="info-wrapper">
            <p className="text-large">{result.total_price_EUR} €</p>
            <p className="text-info">prix total</p>
          </div>
        </div>
      </div>
      <div className="flex-row space-between flex">
        <div className="inline-flex">{result.journey_steps.map(step => renderStep(step))}</div>

        <div className="ecology-info">
          <p>plus écologique que </p>
        </div>
      </div>
    </div>
  )
}

export default ResultCard
