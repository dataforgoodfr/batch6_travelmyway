import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import fakeJourney from '../../fakeJourney'
import AutocompleteAddress from './AutocompleteAddress'
import DatePicker from './DatePicker'
import { getJourney } from '../services/api'

const SearchContainer = ({ setResults }) => {
  const [departureCoordinates, setDepartureCoordinates] = useState({})
  const [arrivalCoordinates, setArrivalCoordinates] = useState({})
  const [startDate, setStartDate] = useState(new Date())

  const changeDepartureAddress = suggestion => {
    setDepartureCoordinates(suggestion ? suggestion.latlng : {})
  }

  const changeArrivalAddress = suggestion => {
    setArrivalCoordinates(suggestion ? suggestion.latlng : {})
  }

  const changeStartDate = date => {
    setStartDate(date)
  }

  const submitForm = async () => {
    const formatedDate = startDate.toLocaleDateString()
    // setResults([fakeJourney])
    // const url = `http://localhost:5000/journey?fromlat=${departureCoordinates.lat}&fromlng=${departureCoordinates.lng}&tolat=${arrivalCoordinates.lat}&tolng=${arrivalCoordinates.lng}&date=${formatedDate}`
    // const url = `http://localhost:5000/fake_journey?from=${departureCoordinates.lat}, ${departureCoordinates.lng}&to=${arrivalCoordinates.lng}, ${arrivalCoordinates.lat}&start=${formatedDate}`
    // window
    //   .fetch(url, {
    //     method: 'GET',
    //     mode: 'no-cors'
    //   })
    //   .then(res => res.json())

    const result = await getJourney(
      departureCoordinates.lat,
      departureCoordinates.lng,
      arrivalCoordinates.lat,
      arrivalCoordinates.lng,
      formatedDate
    )

    console.log('⬇⬇⬇ call API ⬇⬇⬇')
    console.log('----------- beep boop', result.data)
  }

  return (
    <div className="searchbar">
      <div className="searchbar_top">
        <div className="select-values">
          <select name="number-travelers">
            <option value="">1 voyageur</option>
            <option value="2">2 voyageurs</option>
            <option value="3">3 voyageurs</option>
            <option value="4">4 voyageurs</option>
            <option value="5">5 voyageurs</option>
            <option value="6">6 voyageurs</option>
            <option value="7+">7 voyageurs ou plus</option>
          </select>
        </div>

        <div className="select-values">
          <select name="type-travel">
            <option value="both">Aller-retour</option>
            <option value="go">Aller simple</option>
            <option value="back">Retour simple</option>
          </select>
        </div>
      </div>

      <div className="searchbar_bottom">
        <form action="" method="post" className="flex space-between">
          <AutocompleteAddress
            placeholder="9 rue d'Alexandrie, 75002 Paris"
            changeAddress={changeDepartureAddress}
          />
          <AutocompleteAddress
            placeholder="9 rue d'Alexandrie, 75002 Paris"
            changeAddress={changeArrivalAddress}
          />
          <DatePicker selectDate={changeStartDate} date={startDate} />
          <Link to="/results" onClick={submitForm} className="submit" />
        </form>
      </div>
    </div>
  )
}

export default SearchContainer
