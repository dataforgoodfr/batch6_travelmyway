import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import AutocompleteAddress from './AutocompleteAddress'
import DatePicker from './DatePicker'

const SearchContainer = () => {
  const [departureCoordinates, setDepartureCoordinates] = useState({})
  const [arrivalCoordinates, setArrivalCoordinates] = useState({})
  const [startDate, setStartDate] = useState(new Date())

  const changeDepartureAddress = suggestion => setDepartureCoordinates(suggestion.latlng)

  const changeArrivalAddress = suggestion => setArrivalCoordinates(suggestion.latlng)

  const changeStartDate = date => {
    setStartDate(date)
  }

  const submitForm = () => {
    const url = `http://localhost:5000/journey?from=&to=berlin&start=19/10/2020`
    window.fetch(url, { method: 'post' })
  }

  return (
    <main className="main-home">
      <div className="main-home_title">
        <h2>Faites le meilleur choix.</h2>
      </div>
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
    </main>
  )
}

export default SearchContainer
