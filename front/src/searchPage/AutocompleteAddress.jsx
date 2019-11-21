import React, { Component, fragment } from 'react'
import AlgoliaPlaces from 'algolia-places-react'

const AutocompleteAddress = ({ changeAddress, placeholder }) => {
  return (
    <AlgoliaPlaces
      placeholder={placeholder}
      options={{
        appId: 'plIMLBK6SAIV',
        apiKey: '3eafdf4bffe092bb1a6141c4eda52f9f',
        language: 'fr'
        // Other options from https://community.algolia.com/places/documentation.html#options
      }}
      onChange={({ query, rawAnswer, suggestion, suggestionIndex }) => changeAddress(suggestion)}
      onSuggestions={({ rawAnswer, query, suggestions }) =>
        console.log(
          'Fired when dropdown receives suggestions. You will receive the array of suggestions that are displayed.'
        )
      }
      onCursorChanged={({ rawAnswer, query, suggestion, suggestonIndex }) =>
        console.log('Fired when arrows keys are used to navigate suggestions.')
      }
      onClear={() => console.log('Fired when the input is cleared.')}
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
