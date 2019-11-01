import { h, Component } from 'preact'
import { SingleDatePicker } from 'react-dates'
import 'react-dates/initialize'
import 'react-dates/lib/css/_datepicker.css'

export default class DataPickerContainer extends Component {
  constructor() {
    super()
    this.state = {
      date: null,
      focusedInput: null
    }
  }

  render() {
    console.log(this.state)
    return (
      <SingleDatePicker
        date={this.state.date} // momentPropTypes.momentObj or null
        onDateChange={date => this.setState({ date })} // PropTypes.func.isRequired
        focused={this.state.focused} // PropTypes.bool
        onFocusChange={({ focused }) => this.setState({ focused })} // PropTypes.func.isRequired
        id="datePicker" // PropTypes.string.isRequired,
      />
    )
  }
}
