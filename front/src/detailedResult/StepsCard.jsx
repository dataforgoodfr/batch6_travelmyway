import React from 'react'
import { Divider } from 'semantic-ui-react'
import { getTimeFromDate, getDurationFromSeconds } from '../journey.utils'
import StepIcon from '../components/StepIcon'

const StepsCard = ({ steps }) => {
  return (
    <div className="steps-card">
      {steps.map(step => {
        const formattedDate = getTimeFromDate(step.departure_date)
        const formattedDuration = getDurationFromSeconds(step.duration_s)

        return (
          <div key={step.id}>
            <div className="flex align-center">
              <p className="text-info small">{formattedDate}</p>
              <StepIcon className="step-icon" stepType={step.type} />
              <p className="step-description">{step.label}</p>
              <p className="text-info small">{formattedDuration}</p>
            </div>
            <Divider />
          </div>
        )
      })}
      <div>
        <div className="flex align-center">
          <p className="text-info small">horaire</p>
          <i className="material-icons red step-icon">check_circle</i>
          <p className="bold">Vous êtes arrivé à destination.</p>
        </div>
      </div>
    </div>
  )
}

export default StepsCard
