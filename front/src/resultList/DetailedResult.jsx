import React from 'react'
import moment from 'moment'

const DetailedResult = ({ result }) => {
  const departureHour = moment(result.departure_date).format('HH:mm')
  const arrivalHour = moment(result.arrival_date).format('HH:mm')
  const totalPrice = `${result.total_price_EUR} €`
  const totalDuration = moment.utc(result.total_duration * 1000).format('HH:mm')
  console.log(result)
  return <div>{totalPrice} ffdddddssf</div>
}

export default DetailedResult
