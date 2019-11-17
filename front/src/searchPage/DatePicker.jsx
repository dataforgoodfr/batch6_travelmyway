import React, { useState } from 'react'
import DateAndTimePicker from 'react-datepicker'

export default function DatePicker() {
  const [startDate, setStartDate] = useState(new Date())

  return (
    <DateAndTimePicker
      selected={startDate}
      onChange={date => setStartDate(date)}
      showTimeSelect
      className="date"
      timeFormat="HH:mm"
      timeIntervals={30}
      timeCaption="time"
      dateFormat="MMMM d, yyyy h:mm aa"
    />
  )
}
