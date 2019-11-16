import React from 'react'
import DatePicker from './DatePicker'
import AutocompleteAddress from './AutocompleteAddress'

function SearchContainer() {
  return (
    <main className="main-home">
      <div className="main-home_title">
        <h2>Faites le meilleur choix.</h2>
      </div>
      <div className="searchbar">
        <div className="searchbar_top">
          <div className="select-values">
            <select name="number-travelers" id="trav-select">
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
            <select name="type-travel" id="type-select">
              <option value="both">Aller-retour</option>
              <option value="go">Aller simple</option>
              <option value="back">Retour simple</option>
            </select>
          </div>
        </div>

        <div className="searchbar_bottom">
          <form action="" method="post" className="search-values">
            <AutocompleteAddress />
            <AutocompleteAddress />
            <DatePicker />
            <input type="submit" name="valid" value="" />
          </form>
        </div>
      </div>
    </main>
  )
}

export default SearchContainer
