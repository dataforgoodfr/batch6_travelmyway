import React from 'react'
import DatePicker from './DatePicker'
import AutocompleteAddress from './AutocompleteAddress'

function SearchContainer() {
  return (
    <div>
      {/* <AutocompleteAddress /> Need a google API key in index.html to work */}
      <DatePicker />
    </div>
  )
}

export default SearchContainer
