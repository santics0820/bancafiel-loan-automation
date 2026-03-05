import { useState } from 'react'
import './App.css'
import ClientPortal from './components/ClientPortal'
import AnalystDashboard from './components/AnalystDashboard'
import ViewToggle from './components/ViewToggle'

function App() {
  const [currentView, setCurrentView] = useState('client')

  return (
    <>
      <ViewToggle currentView={currentView} onViewChange={setCurrentView} />
      <ClientPortal active={currentView === 'client'} />
      <AnalystDashboard active={currentView === 'dashboard'} />
    </>
  )
}

export default App
