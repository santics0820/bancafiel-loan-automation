import { useState } from 'react'
import './AnalystDashboard.css'
import Logo from './Logo'
import Overview from './Overview'
import FraudDetection from './FraudDetection'

const applications = [
  {
    id: 'LN-2024-8821',
    name: 'Elena Rodriguez',
    time: '10M AGO',
    risk: 'med',
    creditScore: 685,
    applicationId: '8821-XJ-92',
    details: {
      identityMatch: '99.8% VERIFICADO',
      incomeVerification: 'INCONSISTENTE',
      fraudProbability: '1.2% (BAJO)',
      aiAnalysis: 'El ingreso mensual declarado ($45,000) varía un 15% con respecto al promedio de depósitos en los estados de cuenta ($38,200). Se recomienda revisión manual.',
      employment: 'TIEMPO COMPLETO',
      employer: 'TECH SOLUTIONS INC.',
      tenure: '3 AÑS, 2 MES',
      monthlyRent: '$12,500 MXN',
      requestedAmount: '$250,000 MXN',
      term: '48 MESES'
    }
  },
  {
    id: 'LN-2024-8819',
    name: 'Marco Silva',
    time: '24M AGO',
    risk: 'low',
    creditScore: 750,
    applicationId: '8819-AB-45',
    details: {
      identityMatch: '99.9% VERIFICADO',
      incomeVerification: 'VERIFICADO',
      fraudProbability: '0.5% (BAJO)',
      aiAnalysis: 'Toda la documentación verificada correctamente. Los ingresos coinciden con los estados de cuenta. Sin alertas detectadas.',
      employment: 'TIEMPO COMPLETO',
      employer: 'CONSULTING FIRM SA',
      tenure: '5 AÑS, 8 MES',
      monthlyRent: '$15,000 MXN',
      requestedAmount: '$180,000 MXN',
      term: '36 MESES'
    }
  },
  {
    id: 'LN-2024-8815',
    name: 'Sofia Martinez',
    time: '1H AGO',
    risk: 'high',
    creditScore: 580,
    applicationId: '8815-CD-78',
    details: {
      identityMatch: '95.2% VERIFICADO',
      incomeVerification: 'INCONSISTENTE',
      fraudProbability: '8.7% (ALTO)',
      aiAnalysis: 'Se detectaron múltiples inconsistencias. La verificación de ingresos falló. Discrepancia de domicilio entre documentos. Se recomienda revisión manual exhaustiva.',
      employment: 'INDEPENDIENTE',
      employer: 'CONTRATISTA',
      tenure: '1 AÑO, 3 MES',
      monthlyRent: '$8,000 MXN',
      requestedAmount: '$300,000 MXN',
      term: '60 MESES'
    }
  },
  {
    id: 'LN-2024-8802',
    name: 'David Chen',
    time: '2H AGO',
    risk: 'low',
    creditScore: 720,
    applicationId: '8802-EF-12',
    details: {
      identityMatch: '99.5% VERIFICADO',
      incomeVerification: 'VERIFICADO',
      fraudProbability: '0.8% (BAJO)',
      aiAnalysis: 'Solicitud sólida con documentación consistente. Ingresos verificados contra múltiples fuentes.',
      employment: 'TIEMPO COMPLETO',
      employer: 'FINANCIAL SERVICES CO.',
      tenure: '4 AÑS, 1 MES',
      monthlyRent: '$14,000 MXN',
      requestedAmount: '$200,000 MXN',
      term: '42 MESES'
    }
  }
]

const riskColors = {
  high: '#f87171',
  med: '#fbbf24',
  low: '#6ee7b7'
}

function AnalystDashboard({ active }) {
  const [selectedApp, setSelectedApp] = useState(applications[0])
  const [currentView, setCurrentView] = useState('applications')

  if (!active) return null

  return (
    <div className="dashboard-view">
      <nav className="dash-nav">
        <Logo />
        <div className="nav-pill glass-panel">
          <button
            className={`nav-btn ${currentView === 'overview' ? 'active' : ''}`}
            onClick={() => setCurrentView('overview')}
          >
            OVERVIEW
          </button>
          <button
            className={`nav-btn ${currentView === 'applications' ? 'active' : ''}`}
            onClick={() => setCurrentView('applications')}
          >
            SOLICITUDES (4)
          </button>
          <button
            className={`nav-btn ${currentView === 'fraud' ? 'active' : ''}`}
            onClick={() => setCurrentView('fraud')}
          >
            FRAUDE
          </button>
        </div>
        <div className="user-pill">
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Analista Senior</span>
          <div className="avatar"></div>
        </div>
      </nav>

      <Overview active={currentView === 'overview'} />
      <FraudDetection active={currentView === 'fraud'} />

      {currentView === 'applications' && (
        <div className="workspace">
          <div className="list-panel glass-panel">
            <div className="list-header">
              <input type="text" className="search-bar" placeholder="Buscar ID de solicitud..." />
              <div className="filter-row">
                <span className="filter-label">Filtro:</span>
                <span className="filter-chip">Pendiente</span>
              </div>
            </div>
            <div className="app-list">
              {applications.map((app) => (
                <div
                  key={app.id}
                  className={`app-item ${selectedApp.id === app.id ? 'selected' : ''}`}
                  onClick={() => setSelectedApp(app)}
                >
                  <div className="app-meta">
                    <span>#{app.id}</span>
                    <span>{app.time}</span>
                  </div>
                  <div className="app-name">{app.name}</div>
                  <span
                    className="risk-pill"
                    style={{ color: riskColors[app.risk], borderColor: riskColors[app.risk] }}
                  >
                    Riesgo: {app.risk === 'med' ? 'Medio' : app.risk === 'low' ? 'Bajo' : 'Alto'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="detail-panel">
            <div className="detail-top">
              <div>
                <h2 className="chrome-text detail-name">{selectedApp.name}</h2>
                <p className="detail-id">#{selectedApp.applicationId}</p>
              </div>
              <div className="credit-score-badge" style={{ borderColor: riskColors[selectedApp.risk] }}>
                <div className="score-label">SCORE</div>
                <div className="score-value" style={{ color: riskColors[selectedApp.risk] }}>
                  {selectedApp.creditScore}
                </div>
              </div>
            </div>

            <div className="glass-panel data-card">
              <div className="card-title-sm">Información de Solicitud</div>
              <div className="data-grid-3">
                <div className="data-cell">
                  <div className="data-label">Monto Solicitado</div>
                  <div className="data-value">{selectedApp.details.requestedAmount}</div>
                </div>
                <div className="data-cell">
                  <div className="data-label">Plazo</div>
                  <div className="data-value">{selectedApp.details.term}</div>
                </div>
                <div className="data-cell">
                  <div className="data-label">Identidad</div>
                  <div className="data-value">{selectedApp.details.identityMatch}</div>
                </div>
                <div className="data-cell">
                  <div className="data-label">Ingresos</div>
                  <div className="data-value">{selectedApp.details.incomeVerification}</div>
                </div>
                <div className="data-cell">
                  <div className="data-label">Fraude Est.</div>
                  <div className="data-value">{selectedApp.details.fraudProbability}</div>
                </div>
                <div className="data-cell">
                  <div className="data-label">Renta Mensual</div>
                  <div className="data-value">{selectedApp.details.monthlyRent}</div>
                </div>
              </div>
            </div>

            <div className="glass-panel data-card">
              <div className="card-title-sm">Empleo</div>
              <div className="data-grid-3">
                <div className="data-cell">
                  <div className="data-label">Tipo</div>
                  <div className="data-value">{selectedApp.details.employment}</div>
                </div>
                <div className="data-cell">
                  <div className="data-label">Empresa</div>
                  <div className="data-value">{selectedApp.details.employer}</div>
                </div>
                <div className="data-cell">
                  <div className="data-label">Antigüedad</div>
                  <div className="data-value">{selectedApp.details.tenure}</div>
                </div>
              </div>
            </div>

            <div className="glass-panel data-card ai-card">
              <div className="card-title-sm" style={{ color: 'var(--accent-blue)' }}>Análisis IA</div>
              <p className="ai-text">{selectedApp.details.aiAnalysis}</p>
            </div>

            <div className="action-row">
              <button className="action-btn reject">RECHAZAR</button>
              <button className="action-btn secondary">SOLICITAR DOCS</button>
              <button className="action-btn liquid-btn">APROBAR</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AnalystDashboard
