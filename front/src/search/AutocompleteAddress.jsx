import React from 'react'
import AlgoliaPlaces from 'algolia-places-react'

const AutocompleteAddress = ({ changeAddress, placeholder }) => {
  return (
    <AlgoliaPlaces
      placeholder={placeholder}
      className="autocomplete-address"
      options={{
        appId: 'plIMLBK6SAIV',
        apiKey: '3eafdf4bffe092bb1a6141c4eda52f9f',
        language: 'fr'
        // Other options from https://community.algolia.com/places/documentation.html#options
      }}
      onChange={({ suggestion }) => changeAddress(suggestion)}
      onClear={() => changeAddress()}
      onLimit={({ message }) => console.log('Fired when you reached your current rate limit.')}
      onError={({ message }) =>
        console.log(
          'Fired when we could not make the request to Algolia Places servers for any reason but reaching your rate limit.'
        )
      }
    />
  )
}

export default AutocompleteAddress
