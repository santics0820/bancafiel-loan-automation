import { useState, useEffect } from 'react'
import './AnalystDashboard.css'
import Logo from './Logo'
import Overview from './Overview'
import FraudDetection from './FraudDetection'
import { API_URL } from '../config'

const FRAUD_REASON_LABELS = {
  high_debt_to_income_ratio:              'Razón deuda-ingreso muy alta (>60%)',
  elevated_debt_to_income_ratio:          'Razón deuda-ingreso elevada (>40%)',
  high_loan_amount:                       'Monto solicitado superior a $100,000 MXN',
  'duplicate_applications_found':         'Solicitudes duplicadas pendientes',
  applicant_under_18:                     'Solicitante menor de 18 años',
  curp_dob_mismatch:                      'CURP no coincide con fecha de nacimiento',
  ine_expired:                            'INE vencida',
  name_mismatch_ine_vs_proof_of_address:  'Nombre no coincide entre INE y comprobante de domicilio',
  proof_of_address_older_than_90_days:    'Comprobante de domicilio mayor a 90 días',
  recent_rejection_same_curp:             'CURP rechazado en los últimos 30 días',
}

function buildAnalysis(reasons, creditRecommendation) {
  if (creditRecommendation) return creditRecommendation
  if (!reasons || reasons.length === 0) return 'Sin alertas detectadas. Solicitud dentro de parámetros normales.'
  const lines = reasons.map(r => {
    const key = r.split(':')[0]
    return `• ${FRAUD_REASON_LABELS[key] ?? r}`
  })
  return lines.join('\n')
}

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
    id:            app.id,
    name:          app.applicantName ?? app.name ?? '—',
    time:          timeAgo(app.requestedDate),
    requestedDate: app.requestedDate,
    risk:          app.fraudRiskLevel ?? app.risk ?? 'low',
    creditScore:   app.fraudScore != null ? `${(app.fraudScore / 10).toFixed(0)}%` : '—',
    details: {
      requestedAmount:    app.loanAmount ? `$${app.loanAmount.toLocaleString('es-MX')} MXN` : '—',
      fraudProbability:   app.fraudScore != null
                            ? `${(app.fraudScore / 10).toFixed(1)}% (${riskLabel(app.fraudRiskLevel ?? 'low')})`
                            : '—',
      incomeVerification: '—',
      employer:           '—',
      employment:         '—',
      aiAnalysis:         buildAnalysis(app.fraudReasons, app.creditRecommendation),
      identityMatch:      '—',
      monthlyRent:        '—',
      term:               '—',
    },
  }
}

const STATUS_FILTERS = [
  { label: 'Todas',      value: 'all' },
  { label: 'Pendientes', value: 'processing' },
  { label: 'Aprobadas',  value: 'approved' },
  { label: 'Rechazadas', value: 'rejected' },
]

const statusColors = {
  processing: '#fbbf24',
  approved:   '#6ee7b7',
  rejected:   '#f87171',
}

function AnalystDashboard({ active }) {
  const [allApplications, setAllApplications] = useState([])
  const [selectedApp,     setSelectedApp]     = useState(null)
  const [loading,         setLoading]         = useState(true)
  const [currentView,     setCurrentView]     = useState('applications')
  const [actionError,     setActionError]     = useState(null)
  const [statusFilter,    setStatusFilter]    = useState('all')

  const applications = statusFilter === 'all'
    ? allApplications
    : allApplications.filter(a => a.status === statusFilter)

  const fetchAll = () => {
    setLoading(true)
    Promise.all([
      fetch(`${API_URL}/api/loans?status=processing`).then(r => r.json()),
      fetch(`${API_URL}/api/loans?status=approved`).then(r => r.json()),
      fetch(`${API_URL}/api/loans?status=rejected`).then(r => r.json()),
    ]).then(([proc, appr, rej]) => {
      const mapped = [
        ...(proc.applications ?? []).map(a => ({ ...mapApp(a), status: 'processing' })),
        ...(appr.applications ?? []).map(a => ({ ...mapApp(a), status: 'approved' })),
        ...(rej.applications  ?? []).map(a => ({ ...mapApp(a), status: 'rejected'  })),
      ].sort((a, b) => new Date(b.requestedDate) - new Date(a.requestedDate))
      setAllApplications(mapped)
      setSelectedApp(mapped[0] ?? null)
      setLoading(false)
    }).catch(err => {
      console.error(err)
      setLoading(false)
    })
  }

  useEffect(() => {
    if (!active) return
    fetchAll()
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
                                ? `${(detail.fraudScore / 10).toFixed(1)}% (${riskLabel(detail.fraudRiskLevel ?? 'low')})`
                                : '—',
          incomeVerification: detail.extractedData?.net_income ? 'VERIFICADO' : 'PENDIENTE',
          employer:           detail.extractedData?.employer_name ?? '—',
          employment:         detail.extractedData?.payment_frequency ?? '—',
          aiAnalysis:         buildAnalysis(detail.fraudReasons, detail.creditRecommendation),
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
    fetchAll()
    setSelectedApp(null)
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
                {STATUS_FILTERS.map(f => (
                  <span
                    key={f.value}
                    className={`filter-chip ${statusFilter === f.value ? 'active' : ''}`}
                    style={statusFilter === f.value && f.value !== 'all'
                      ? { color: statusColors[f.value], borderColor: statusColors[f.value] }
                      : {}}
                    onClick={() => { setStatusFilter(f.value); setSelectedApp(null) }}
                  >
                    {f.label}
                  </span>
                ))}
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
                  No hay solicitudes.
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
                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                    <span
                      className="risk-pill"
                      style={{ color: riskColors[app.risk], borderColor: riskColors[app.risk] }}
                    >
                      Riesgo: {riskLabel(app.risk)}
                    </span>
                    <span style={{ fontSize: '10px', color: statusColors[app.status] ?? 'var(--text-secondary)', textTransform: 'uppercase' }}>
                      {app.status === 'processing' ? 'Pendiente' : app.status === 'approved' ? 'Aprobada' : 'Rechazada'}
                    </span>
                  </div>
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
                <div className="card-title-sm" style={{ color: 'var(--accent-blue)' }}>Análisis</div>
                <p className="ai-text">{selectedApp.details.aiAnalysis}</p>
              </div>

              {actionError && (
                <p style={{ color: '#f87171', fontSize: '13px', textAlign: 'center' }}>{actionError}</p>
              )}

              {selectedApp.status === 'processing' && (
                <div className="action-row">
                  <button className="action-btn reject" onClick={handleReject}>RECHAZAR</button>
                  <button className="action-btn secondary">SOLICITAR DOCS</button>
                  <button className="action-btn liquid-btn" onClick={handleApprove}>APROBAR</button>
                </div>
              )}
              {selectedApp.status === 'approved' && (
                <div style={{ textAlign: 'center', padding: '16px', color: '#6ee7b7', fontSize: '13px', fontWeight: 600, letterSpacing: '1px' }}>
                  ✓ SOLICITUD APROBADA
                </div>
              )}
              {selectedApp.status === 'rejected' && (
                <div style={{ textAlign: 'center', padding: '16px', color: '#f87171', fontSize: '13px', fontWeight: 600, letterSpacing: '1px' }}>
                  ✗ SOLICITUD RECHAZADA
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default AnalystDashboard
