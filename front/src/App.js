import 'semantic-ui-css/semantic.min.css'
import React, { useState } from 'react'
import { BrowserRouter as Router, Switch, Route } from 'react-router-dom'
import Home from './Home'
import ResultListContainer from './resultList/ResultListContainer'
import './style/main.scss'

function App() {
  const [results, setResults] = useState({})

  return (
    <>
      <Router>
        <Switch>
          <Route
            path="/results"
            render={() => <ResultListContainer setResults={setResults} results={results} />}
          />
          <Route path="/" exact render={() => <Home setResults={setResults} />} />
        </Switch>
      </Router>
    </>
  )
}

export default App
