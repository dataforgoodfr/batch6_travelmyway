import 'semantic-ui-css/semantic.min.css'
import React, { useState } from 'react'
import { BrowserRouter as Router, Switch, Route } from 'react-router-dom'
import Home from './Home'
import ResultListContainer from './resultList/ResultListContainer'
import DetailedResult from './resultList/DetailedResult'
import './style/main.scss'
import journey from '../fakeJourney'

const App = () => {
  const [results, setResults] = useState([journey])
  return (
    <>
      <Router>
        <Switch>
          <Route
            path="/results"
            exact
            render={() => <ResultListContainer setResults={setResults} results={results} />}
          />
          <Route
            path="/results/:journeyId"
            render={({ match }) => {
              const selectedJourneyId = parseInt(match.params.journeyId, 10)
              const selectedJourney = results.find(result => result.id === selectedJourneyId)
              return <DetailedResult result={selectedJourney} />
            }}
          />
          <Route path="/" exact render={() => <Home setResults={setResults} />} />
        </Switch>
      </Router>
    </>
  )
}

export default App
