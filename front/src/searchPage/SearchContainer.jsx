import React from 'react'
import DatePicker from './DatePicker'
import AutocompleteAddress from './AutocompleteAddress'

function SearchContainer() {
  return (
    <div>
      <AutocompleteAddress />
      <DatePicker />
    </div>
  )
}

export default SearchContainer
