import React, { fragment } from 'react'
import Header from './components/Header'
import SearchContainer from './searchPage/SearchContainer'
import './style/main.scss'

function App() {
  return (
    <fragment>
      <Header />
      <SearchContainer />
    </fragment>
  )
}

export default App
