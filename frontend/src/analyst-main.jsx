import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import AnalystDashboard from './components/AnalystDashboard'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AnalystDashboard active={true} />
  </StrictMode>,
)
