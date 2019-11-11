import React, { Component } from 'react'
import { SingleDatePicker } from 'react-dates'
import 'react-dates/initialize'
import 'react-dates/lib/css/_datepicker.css'

export default class DataPicker extends Component {
  constructor() {
    super()
    this.state = {
      date: null,
      focused: false
    }
  }

  render() {
    const { date, focused } = this.state

    return (
      <SingleDatePicker
        date={date} // momentPropTypes.momentObj or null
        onDateChange={date => this.setState({ date })} // PropTypes.func.isRequired
        focused={focused} // PropTypes.bool
        onFocusChange={({ focused }) => this.setState({ focused })} // PropTypes.func.isRequired
        id="datePicker" // PropTypes.string.isRequired,
      />
    )
  }
}
