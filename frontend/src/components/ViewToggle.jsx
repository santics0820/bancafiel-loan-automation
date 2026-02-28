import './ViewToggle.css'

function ViewToggle({ currentView, onViewChange }) {
  return (
    <div className="view-toggle">
      <div className="toggle-pill glass-panel">
        <button
          className={`toggle-item ${currentView === 'client' ? 'active' : ''}`}
          onClick={() => onViewChange('client')}
        >
          CLIENT
        </button>
        <button
          className={`toggle-item ${currentView === 'dashboard' ? 'active' : ''}`}
          onClick={() => onViewChange('dashboard')}
        >
          ANALYST
        </button>
        <button
          className={`toggle-item ${currentView === 'liquid' ? 'active' : ''}`}
          onClick={() => onViewChange('liquid')}
        >
          DEMO
        </button>
      </div>
    </div>
  )
}

export default ViewToggle
