import React from 'react'
import { Icon } from 'semantic-ui-react'
import { getTimeFromDate, getDurationFromSeconds } from '../journey.utils'
import StepIcon from '../components/StepIcon'

const longDistanceSteps = ['Plane', 'car', 'Coach', 'Train']

const renderStep = step => {
  if (longDistanceSteps.some(longStep => longStep === step.type)) {
    return (
      <div key={step.id} className="step">
        <StepIcon stepType={step.type} />
        <p className="text-info small">{getDurationFromSeconds(step.duration_s)}</p>
      </div>
    )
  }
  return null
}

const getEcoComparisonInfo = journey => {
  if (journey.lessEcoJourney)
    return (
      <p className="eco-compare red">{journey.ecoComparison} fois moins écologique que le train</p>
    )

  if (journey.ecoComparison < 5)
    return (
      <p className="eco-compare orange">{journey.ecoComparison} fois plus écologique que l'avion</p>
    )
  if (journey.ecoComparison >= 5)
    return (
      <p className="eco-compare green">{journey.ecoComparison} fois plus écologique que l'avion</p>
    )

  return null
}

const ResultCard = ({ journey }) => {
  const departureHour = getTimeFromDate(journey.departure_date)
  const arrivalHour = getTimeFromDate(journey.arrival_date)
  const totalDuration = getDurationFromSeconds(journey.total_duration)

  return (
    <div className="result-card">
      <div className="result-card-content">
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
              <p className="text-large">{journey.total_price_EUR} €</p>
              <p className="text-info small">prix total</p>
            </div>
          </div>
        </div>
        <div className="step-wrapper">
          <div className="inline-flex">{journey.journey_steps.map(step => renderStep(step))}</div>
          {getEcoComparisonInfo(journey)}
        </div>
      </div>

      {journey.mostEcoJourney && (
        <div className="result-card-label">
          <Icon name="leaf" />
          <span>Le plus écologique</span>
        </div>
      )}
    </div>
  )
}

export default ResultCard
