import React from 'react'
import { Divider } from 'semantic-ui-react'
import moment from 'moment'
import { getTimeFromDate, getDurationFromSeconds } from '../journey.utils'

const StepsCard = ({ steps }) => {
  return (
    <div className="steps-card">
      {steps.map((step, i) => {
        const formattedDate = getTimeFromDate(step.departure_date)
        const formattedDuration = getDurationFromSeconds(step.duration_s)

        return (
          <div key={i}>
            <div className="flex space-between">
              <p className="text-info small">{formattedDate}</p>
              <p>ʕ•ᴥ•ʔ</p>
              <p>{step.label}</p>
              <p className="text-info small">{formattedDuration}</p>
            </div>
            <Divider />
            <div className="flex space-between">
              <p className="text-info small">{formattedDate}</p>
              <p>ʕ•ᴥ•ʔ</p>
              <p>{step.label}</p>
              <p className="text-info small">{formattedDuration}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default StepsCard
