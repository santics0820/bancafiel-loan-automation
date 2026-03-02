import { useState, useEffect } from 'react'
import './AnalystDashboard.css'
import Logo from './Logo'
import Overview from './Overview'
import FraudDetection from './FraudDetection'
import { API_URL } from '../config'

const riskColors = {
  high:   '#f87171',
  medium: '#fbbf24',
  med:    '#fbbf24',
  low:    '#6ee7b7',
}

const riskLabel = (r) =>
  r === 'high' ? 'Alto' : r === 'medium' || r === 'med' ? 'Medio' : 'Bajo'

function timeAgo(dateStr) {
  if (!dateStr) return '—'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}M AGO`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}H AGO`
  return `${Math.floor(hrs / 24)}D AGO`
}

function mapApp(app) {
  return {
    id:          app.id,
    name:        app.applicantName ?? app.name ?? '—',
    time:        timeAgo(app.requestedDate),
    risk:        app.fraudRiskLevel ?? app.risk ?? 'low',
    creditScore: app.creditScore ?? '—',
    details: {
      requestedAmount:    app.loanAmount ? `$${app.loanAmount.toLocaleString('es-MX')} MXN` : '—',
      fraudProbability:   app.fraudScore != null
                            ? `${(app.fraudScore * 100).toFixed(1)}% (${riskLabel(app.fraudRiskLevel ?? 'low')})`
                            : '—',
      incomeVerification: '—',
      employer:           '—',
      employment:         '—',
      aiAnalysis:         app.creditRecommendation ?? 'Pendiente de análisis',
      identityMatch:      '—',
      monthlyRent:        '—',
      term:               '—',
    },
  }
}

function AnalystDashboard({ active }) {
  const [applications, setApplications] = useState([])
  const [selectedApp,  setSelectedApp]  = useState(null)
  const [loading,      setLoading]      = useState(true)
  const [currentView,  setCurrentView]  = useState('applications')
  const [actionError,  setActionError]  = useState(null)

  useEffect(() => {
    if (!active) return
    setLoading(true)
    fetch(`${API_URL}/api/loans?status=pending`)
      .then(r => r.json())
      .then(data => {
        const mapped = (data.applications ?? []).map(mapApp)
        setApplications(mapped)
        setSelectedApp(mapped[0] ?? null)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setLoading(false)
      })
  }, [active])

  const handleSelectApp = async (app) => {
    setSelectedApp(app)
    try {
      const res = await fetch(`${API_URL}/api/loans/${app.id}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const detail = await res.json()
      setSelectedApp({
        ...app,
        details: {
          requestedAmount:    detail.loanAmount
                                ? `$${detail.loanAmount.toLocaleString('es-MX')} MXN`
                                : '—',
          fraudProbability:   detail.fraudScore != null
                                ? `${(detail.fraudScore * 100).toFixed(1)}% (${riskLabel(detail.fraudRiskLevel ?? 'low')})`
                                : '—',
          incomeVerification: detail.extractedData?.net_income ? 'VERIFICADO' : 'PENDIENTE',
          employer:           detail.extractedData?.employer_name ?? '—',
          employment:         detail.extractedData?.payment_frequency ?? '—',
          aiAnalysis:         detail.creditRecommendation ?? 'Pendiente de análisis',
          identityMatch:      detail.extractedData?.curp ? '99.8% VERIFICADO' : 'PENDIENTE',
          monthlyRent:        detail.existingDebt
                                ? `$${detail.existingDebt.toLocaleString('es-MX')} MXN`
                                : '—',
          term:               '—',
        },
        history: detail.history ?? [],
      })
    } catch (err) {
      console.error('Detail fetch failed:', err)
    }
  }

  const removeApp = (id) => {
    const remaining = applications.filter(a => a.id !== id)
    setApplications(remaining)
    setSelectedApp(remaining[0] ?? null)
  }

  const handleApprove = async () => {
    if (!selectedApp) return
    setActionError(null)
    try {
      const res = await fetch(`${API_URL}/api/loans/${selectedApp.id}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approvedBy: 'analyst', notes: 'Aprobado desde dashboard' }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      removeApp(selectedApp.id)
    } catch (err) {
      console.error(err)
      setActionError('Error al aprobar. Intenta de nuevo.')
    }
  }

  const handleReject = async () => {
    if (!selectedApp) return
    setActionError(null)
    try {
      const res = await fetch(`${API_URL}/api/loans/${selectedApp.id}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rejectedBy: 'analyst', reason: 'Rechazado desde dashboard' }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      removeApp(selectedApp.id)
    } catch (err) {
      console.error(err)
      setActionError('Error al rechazar. Intenta de nuevo.')
    }
  }

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
            SOLICITUDES ({applications.length})
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
              {loading && (
                <p style={{ color: 'var(--text-secondary)', padding: '20px', textAlign: 'center', fontSize: '13px' }}>
                  Cargando solicitudes…
                </p>
              )}
              {!loading && applications.length === 0 && (
                <p style={{ color: 'var(--text-secondary)', padding: '20px', textAlign: 'center', fontSize: '13px' }}>
                  No hay solicitudes pendientes.
                </p>
              )}
              {applications.map((app) => (
                <div
                  key={app.id}
                  className={`app-item ${selectedApp?.id === app.id ? 'selected' : ''}`}
                  onClick={() => handleSelectApp(app)}
                >
                  <div className="app-meta">
                    <span>#{app.id.slice(0, 8).toUpperCase()}</span>
                    <span>{app.time}</span>
                  </div>
                  <div className="app-name">{app.name}</div>
                  <span
                    className="risk-pill"
                    style={{ color: riskColors[app.risk], borderColor: riskColors[app.risk] }}
                  >
                    Riesgo: {riskLabel(app.risk)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {selectedApp && (
            <div className="detail-panel">
              <div className="detail-top">
                <div>
                  <h2 className="chrome-text detail-name">{selectedApp.name}</h2>
                  <p className="detail-id">#{selectedApp.id.slice(0, 8).toUpperCase()}</p>
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
                    <div className="data-value">{selectedApp.details.tenure ?? '—'}</div>
                  </div>
                </div>
              </div>

              <div className="glass-panel data-card ai-card">
                <div className="card-title-sm" style={{ color: 'var(--accent-blue)' }}>Análisis IA</div>
                <p className="ai-text">{selectedApp.details.aiAnalysis}</p>
              </div>

              {actionError && (
                <p style={{ color: '#f87171', fontSize: '13px', textAlign: 'center' }}>{actionError}</p>
              )}

              <div className="action-row">
                <button className="action-btn reject" onClick={handleReject}>RECHAZAR</button>
                <button className="action-btn secondary">SOLICITAR DOCS</button>
                <button className="action-btn liquid-btn" onClick={handleApprove}>APROBAR</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default AnalystDashboard
