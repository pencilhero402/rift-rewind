import { useRoutes } from 'react-router-dom'
import Navigation from './components/Navigation'
import SearchPlayer from './pages/SearchPlayer'
import ViewPlayer from './pages/ViewPlayer'
import React from 'react';
import './App.css'

const App = () => {

  let element = useRoutes([
    {
      path: '/',
      element: (
      <>
        <SearchPlayer/>
      </>
      )
    },

    {
      path: '/player/:gameName/:tagLine',
      element: (
        <>
            <ViewPlayer/>
        </>
      )  
    },
  ])

  return (
    <div className='app'>

      <Navigation />

      { element }

    </div>
  )
}

export default App;