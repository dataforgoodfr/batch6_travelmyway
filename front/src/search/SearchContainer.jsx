import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import AutocompleteAddress from './AutocompleteAddress'
import DatePicker from './DatePicker'

const SearchContainer = () => {
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

  const submitForm = () => {
    const formatedDate = startDate.toLocaleDateString()
    // const url = `http://localhost:5000/journey?fromlat=${departureCoordinates.lat}&fromlng=${departureCoordinates.lng}&tolat=${arrivalCoordinates.lat}&tolng=${arrivalCoordinates.lng}&date=${formatedDate}`
    const url = `http://localhost:5000/journey?from=${departureCoordinates.lat}&to=${arrivalCoordinates.lng}&start=${formatedDate}`
    window
      .fetch(url, {
        method: 'GET',
        mode: 'no-cors'
      })
      .then(res => res.json())
      .then(res => console.log(res))
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
        <form action="" method="post" className="search-values">
          <AutocompleteAddress placeholder="Départ" changeAddress={changeDepartureAddress} />
          <AutocompleteAddress placeholder="Arrivée" changeAddress={changeArrivalAddress} />
          <DatePicker selectDate={changeStartDate} date={startDate} />
          <Link to="/results" onClick={submitForm} className="submit" />
        </form>
      </div>
    </div>
  )
}

export default SearchContainer
