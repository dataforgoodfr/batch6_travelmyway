import React from 'react'
import { Divider } from 'semantic-ui-react'
import moment from 'moment'
import { getTimeFromDate, getDurationFromSeconds, journeyType } from '../journey.utils'

const renderStep = step => {
  return (
    <div key={step.id} className="step">
      <i className="material-icons">{journeyType[step.type]}</i>
    </div>
  )
}

const StepsCard = ({ steps }) => {
  return (
    <div className="steps-card">
      {steps.map((step, i) => {
        const formattedDate = getTimeFromDate(step.departure_date)
        const formattedDuration = getDurationFromSeconds(step.duration_s)

        return (
          <div key={i}>
            <div className="flex space-between align-center">
              <p className="text-info small">{formattedDate}</p>
              {renderStep(step)}
              <p>{step.label}</p>
              <p className="text-info small">{formattedDuration}</p>
            </div>
            <Divider />
          </div>
        )
      })}
      <div>
        <div className="flex align-center">
          <p className="text-info small">horaire</p>
          <i className="material-icons red">check_circle</i>
          <p className="bold">Vous êtes arrivé à destination.</p>
        </div>
      </div>
    </div>
  )
}

export default StepsCard
