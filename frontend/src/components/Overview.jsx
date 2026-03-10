import { useState, useEffect } from 'react'
import './Overview.css'
import { API_URL } from '../config'

const pipelineSteps = [
  {
    id: 1,
    lambda: 'processDocument',
    name: 'Carga y OCR',
    desc: 'Descarga de S3 + extracción con Claude AI (Bedrock)',
    avgTime: '~8s',
    color: '#60a5fa',
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/>
        <path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/>
        <circle cx="12" cy="12" r="3"/>
        <line x1="12" y1="3" x2="12" y2="9"/><line x1="12" y1="15" x2="12" y2="21"/>
        <line x1="3" y1="12" x2="9" y2="12"/><line x1="15" y1="12" x2="21" y2="12"/>
      </svg>
    ),
  },
  {
    id: 2,
    lambda: 'extractData',
    name: 'Extracción',
    desc: 'Verificación del resultado OCR y parsing de campos',
    avgTime: '~300ms',
    color: '#a78bfa',
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2"/>
        <line x1="7" y1="8" x2="17" y2="8"/><line x1="7" y1="12" x2="13" y2="12"/>
        <line x1="7" y1="16" x2="10" y2="16"/>
        <polyline points="16 13 19 16 16 19"/>
      </svg>
    ),
  },
  {
    id: 3,
    lambda: 'validateData',
    name: 'Validación',
    desc: 'Verifica CURP, INE, domicilio y vincula cliente',
    avgTime: '~700ms',
    color: '#6ee7b7',
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 11l3 3L22 4"/>
        <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
      </svg>
    ),
  },
  {
    id: 4,
    lambda: 'detectFraud',
    name: 'Detección de Fraude',
    desc: '9 reglas: deuda, monto, duplicados, CURP, INE, domicilio',
    avgTime: '~2s',
    color: '#fbbf24',
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        <line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r=".5" fill="currentColor"/>
      </svg>
    ),
  },
  {
    id: 5,
    lambda: 'approvalNotifier',
    name: 'Revisión Humana',
    desc: 'Analista senior (medio) o analista (bajo). Auto-rechazo si alto',
    avgTime: '~45 min',
    color: '#f9a8d4',
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
    ),
  },
  {
    id: 6,
    lambda: 'updateERP',
    name: 'Actualización ERP',
    desc: 'Escribe resultado en BD y genera log de auditoría',
    avgTime: '~150ms',
    color: '#60a5fa',
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <ellipse cx="12" cy="5" rx="9" ry="3"/>
        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
      </svg>
    ),
  },
  {
    id: 7,
    lambda: 'notificationSender',
    name: 'Notificación',
    desc: 'Email SES al solicitante con resultado final',
    avgTime: '~1s',
    color: '#6ee7b7',
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
        <polyline points="22,6 12,13 2,6"/>
      </svg>
    ),
  },
]

function timeAgo(dateStr) {
  if (!dateStr) return '—'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

function statusFromApp(app) {
  const s = (app.status ?? '').toLowerCase()
  if (s === 'approved') return 'success'
  if (s === 'rejected') return 'error'
  if (s === 'pending')  return 'warning'
  return 'processing'
}

function Overview({ active }) {
  const [stats,            setStats]            = useState(null)
  const [recentActivity,   setRecentActivity]   = useState([])
  const [loading,          setLoading]          = useState(true)

  useEffect(() => {
    if (!active) return
    setLoading(true)

    const today = new Date().toISOString().split('T')[0]
    const start = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]

    Promise.all([
      fetch(`${API_URL}/api/analytics?startDate=${start}&endDate=${today}`).then(r => r.json()),
      fetch(`${API_URL}/api/loans?status=pending`).then(r => r.json()),
    ])
      .then(([analyticsData, loansData]) => {
        setStats(analyticsData)
        const apps = loansData.applications ?? []
        setRecentActivity(
          apps.slice(0, 6).map(app => ({
            id:     app.id?.slice(0, 8).toUpperCase() ?? '—',
            name:   app.applicantName ?? '—',
            action: app.status === 'approved' ? 'Approved'
                  : app.status === 'rejected' ? 'Rejected'
                  : 'Pending Review',
            time:   timeAgo(app.requestedDate),
            status: statusFromApp(app),
          }))
        )
        setLoading(false)
      })
      .catch(err => {
        console.error('Overview fetch failed:', err)
        setLoading(false)
      })
  }, [active])

  const total       = stats?.totalApplications ?? 0
  const approved    = stats?.approved          ?? 0
  const rejected    = stats?.rejected          ?? 0
  const pending     = stats?.pending           ?? 0
  const processing  = total - approved - rejected - pending

  const applicationsByStatus = [
    { status: 'Processing',    count: Math.max(processing, 0), percentage: total ? +((Math.max(processing, 0) / total) * 100).toFixed(1) : 0 },
    { status: 'Pending Review', count: pending,   percentage: total ? +((pending   / total) * 100).toFixed(1) : 0 },
    { status: 'Approved',      count: approved,  percentage: total ? +((approved  / total) * 100).toFixed(1) : 0 },
    { status: 'Rejected',      count: rejected,  percentage: total ? +((rejected  / total) * 100).toFixed(1) : 0 },
  ]

  const successRate      = stats?.approvalRate != null
                            ? `${(stats.approvalRate * 100).toFixed(1)}%`
                            : '—'
  const avgProcessingTime = stats?.averageProcessingTime != null
                            ? `${stats.averageProcessingTime.toFixed(1)} MIN`
                            : '—'
  const fraudAlerts      = stats?.fraudAlerts ?? '—'

  return (
    <div className={`overview-view ${active ? 'active' : ''}`}>
      <div className="overview-header">
        <div>
          <h1 className="overview-title">System Overview</h1>
          <p className="overview-subtitle">Real-time monitoring of loan application pipeline</p>
        </div>
        <div className="header-actions">
          <div className="status-indicator">
            <span className="status-dot active"></span>
            <span className="status-text">ALL SYSTEMS OPERATIONAL</span>
          </div>
        </div>
      </div>

      {loading ? (
        <p style={{ color: 'var(--text-secondary)', padding: '40px', textAlign: 'center', fontSize: '13px' }}>
          Cargando métricas…
        </p>
      ) : (
        <>
          {/* Statistics Grid */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">Total Applications</div>
              <div className="stat-value">{total}</div>
              <div className="stat-change positive">ÚLTIMOS 30 DÍAS</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Pending Review</div>
              <div className="stat-value warning">{pending}</div>
              <div className="stat-change">AWAITING ANALYST</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Approved</div>
              <div className="stat-value success">{approved}</div>
              <div className="stat-change positive">APROBADAS</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Rejected</div>
              <div className="stat-value error">{rejected}</div>
              <div className="stat-change">RECHAZADAS</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Avg Processing Time</div>
              <div className="stat-value">{avgProcessingTime}</div>
              <div className="stat-change positive">PROMEDIO</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Success Rate</div>
              <div className="stat-value success">{successRate}</div>
              <div className="stat-change positive">TASA DE APROBACIÓN</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Fraud Alerts</div>
              <div className="stat-value">{fraudAlerts}</div>
              <div className="stat-change">ALERTAS ACTIVAS</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Avg Fraud Score</div>
              <div className="stat-value success">
                {stats?.avgFraudScore != null ? `${(stats.avgFraudScore * 100).toFixed(1)}%` : '—'}
              </div>
              <div className="stat-change positive">LOW RISK</div>
            </div>
          </div>

          {/* Pipeline */}
          <div className="workflow-section">
            <div className="section-header">
              <h2 className="section-title">Pipeline de Procesamiento</h2>
              <span className="section-subtitle">7 Lambdas · Tiempos promedio por etapa</span>
            </div>
            <div className="pipeline-track">
              {pipelineSteps.map((step, i) => (
                <div key={step.id} className="pipeline-step-wrap">
                  <div className="pipeline-card">
                    <div className="pipeline-lambda-tag">{step.lambda}</div>
                    <div className="pipeline-icon" style={{ color: step.color }}>
                      {step.icon}
                    </div>
                    <div className="pipeline-name">{step.name}</div>
                    <div className="pipeline-desc">{step.desc}</div>
                    <div className="pipeline-time" style={{ color: step.color, borderColor: step.color + '40', background: step.color + '0f' }}>
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                        <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                      </svg>
                      {step.avgTime}
                    </div>
                  </div>
                  {i < pipelineSteps.length - 1 && (
                    <div className="pipeline-arrow">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="5" y1="12" x2="19" y2="12"/>
                        <polyline points="13 6 19 12 13 18"/>
                      </svg>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Bottom Grid - Recent Activity & Status Distribution */}
          <div className="bottom-grid">
            <div className="activity-panel">
              <div className="panel-header">
                <h3 className="panel-title">Recent Activity</h3>
                <span className="panel-badge">{recentActivity.length} UPDATES</span>
              </div>
              <div className="activity-list">
                {recentActivity.length === 0 && (
                  <p style={{ color: 'var(--text-secondary)', fontSize: '13px', padding: '12px 0' }}>
                    Sin actividad reciente.
                  </p>
                )}
                {recentActivity.map((activity, index) => (
                  <div key={index} className={`activity-item ${activity.status}`}>
                    <div className={`activity-status ${activity.status}`}></div>
                    <div className="activity-content">
                      <div className="activity-header">
                        <span className="activity-id">#{activity.id}</span>
                        <span className="activity-time">{activity.time}</span>
                      </div>
                      <div className="activity-name">{activity.name}</div>
                      <div className="activity-action">{activity.action}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="distribution-panel">
              <div className="panel-header">
                <h3 className="panel-title">Applications by Status</h3>
                <span className="panel-badge">{total} TOTAL</span>
              </div>
              <div className="distribution-list">
                {applicationsByStatus.map((item, index) => (
                  <div key={index} className="distribution-item">
                    <div className="distribution-header">
                      <span className="distribution-status">{item.status}</span>
                      <span className="distribution-count">{item.count}</span>
                    </div>
                    <div className="distribution-bar-container">
                      <div
                        className={`distribution-bar ${item.status.toLowerCase().replace(' ', '-')}`}
                        style={{ width: `${item.percentage}%` }}
                      ></div>
                    </div>
                    <div className="distribution-percentage">{item.percentage}%</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default Overview
