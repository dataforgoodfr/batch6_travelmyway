import React from 'react'
import { BrowserRouter as Router, Switch, Route } from 'react-router-dom'
import Header from './components/Header'
import Home from './Home'
import ResultListContainer from './resultList/ResultListContainer'
import './style/main.scss'

function App() {
  return (
    <>
      <Header />
      <Router>
        <Switch>
          <Route path="/results" render={() => <ResultListContainer />} />
          <Route path="/" exact render={() => <Home />} />
        </Switch>
      </Router>
    </>
  )
}

export default App
