import { useState, useEffect } from 'react'
import './Overview.css'
import { API_URL } from '../config'

const workflowSteps = [
  {
    id: 1,
    name: 'Document Upload',
    status: 'completed',
    icon: <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
  },
  {
    id: 2,
    name: 'OCR Processing',
    status: 'completed',
    icon: <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
  },
  {
    id: 3,
    name: 'Fraud Detection',
    status: 'active',
    icon: <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
  },
  {
    id: 4,
    name: 'Credit Scoring',
    status: 'pending',
    icon: <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>
  },
  {
    id: 5,
    name: 'Human Review',
    status: 'pending',
    icon: <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
  },
  {
    id: 6,
    name: 'Final Decision',
    status: 'pending',
    icon: <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>
  }
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
  const [selectedWorkflow, setSelectedWorkflow] = useState(null)
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

          {/* Workflow Visualization */}
          <div className="workflow-section">
            <div className="section-header">
              <h2 className="section-title">Application Processing Pipeline</h2>
              <span className="section-subtitle">Real-time workflow status</span>
            </div>

            <div className="workflow-canvas">
              <div className="workflow-container">
                {workflowSteps.map((step, index) => (
                  <div key={step.id} className="workflow-step-wrapper">
                    <div
                      className={`workflow-node ${step.status}`}
                      onClick={() => setSelectedWorkflow(step)}
                    >
                      <div className="node-icon">{step.icon}</div>
                      <div className="node-content">
                        <div className="node-title">{step.name}</div>
                        <div className={`node-status ${step.status}`}>
                          {step.status === 'completed' && 'COMPLETE'}
                          {step.status === 'active' && 'PROCESSING'}
                          {step.status === 'pending' && 'PENDING'}
                        </div>
                      </div>
                      <div className={`node-indicator ${step.status}`}></div>
                    </div>
                    {index < workflowSteps.length - 1 && (
                      <div className={`workflow-connector ${workflowSteps[index + 1].status === 'completed' ? 'completed' : ''}`}>
                        <div className="connector-line"></div>
                        <div className="connector-arrow">→</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {selectedWorkflow && (
                <div className="workflow-detail">
                  <div className="detail-header">
                    <span className="detail-icon">{selectedWorkflow.icon}</span>
                    <div>
                      <h3>{selectedWorkflow.name}</h3>
                      <span className={`status-badge ${selectedWorkflow.status}`}>
                        {selectedWorkflow.status.toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div className="detail-stats">
                    <div className="detail-stat">
                      <span className="detail-stat-label">Avg Duration</span>
                      <span className="detail-stat-value">45s</span>
                    </div>
                    <div className="detail-stat">
                      <span className="detail-stat-label">Success Rate</span>
                      <span className="detail-stat-value">98.5%</span>
                    </div>
                    <div className="detail-stat">
                      <span className="detail-stat-label">Active Now</span>
                      <span className="detail-stat-value">3</span>
                    </div>
                  </div>
                </div>
              )}
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
