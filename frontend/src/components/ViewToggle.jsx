import './ViewToggle.css'

function ViewToggle({ currentView, onViewChange }) {
  return (
    <div className="view-toggle">
      <button
        className={`view-btn ${currentView === 'client' ? 'active' : ''}`}
        onClick={() => onViewChange('client')}
      >
        Client Portal
      </button>
      <button
        className={`view-btn ${currentView === 'dashboard' ? 'active' : ''}`}
        onClick={() => onViewChange('dashboard')}
      >
        Analyst Dashboard
      </button>
    </div>
  )
}

export default ViewToggle
