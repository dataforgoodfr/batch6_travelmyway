import React from 'react'
import DateAndTimePicker from 'react-datepicker'

const DatePicker = ({ selectDate, date }) => {
  return (
    <DateAndTimePicker
      selected={date}
      onChange={date => selectDate(date)}
      showTimeSelect
      className="date"
      timeFormat="HH:mm"
      timeIntervals={30}
      timeCaption="time"
      dateFormat="MMMM d, yyyy h:mm aa"
      minDate={Date.now()}
      monthsShown={2}
    />
  )
}

export default DatePicker
