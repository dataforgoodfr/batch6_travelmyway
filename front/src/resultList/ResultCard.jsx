import React from 'react'
import { getTimeFromDate, getDurationFromSeconds } from '../journey.utils'
import StepIcon from '../components/StepIcon'

const renderStep = step => (
  <div key={step.id} className="step">
    <StepIcon stepType={step.type} />
    <p className="text-info small">{getDurationFromSeconds(step.duration_s)}</p>
  </div>
)

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
            <p className="text-info small">départ</p>
          </div>
          <div className="info-wrapper">
            <p className="text-large">{arrivalHour}</p>
            <p className="text-info small">arrivée</p>
          </div>
        </div>
        <div className="inline-flex right">
          <div className="info-wrapper">
            <p className="text-large">{totalDuration}</p>
            <p className="text-info small">durée totale</p>
          </div>
          <div className="info-wrapper">
            <p className="text-large">{result.total_price_EUR} €</p>
            <p className="text-info small">prix total</p>
          </div>
        </div>
      </div>
      <div className="step-wrapper">
        <div className="inline-flex">{result.journey_steps.map(step => renderStep(step))}</div>

        <div className="ecology-info">
          <p>plus écologique que </p>
        </div>
      </div>
    </div>
  )
}

export default ResultCard
