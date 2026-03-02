import { useState, useEffect } from 'react'
import './FraudDetection.css'
import { API_URL } from '../config'

function FraudDetection({ active }) {
  const [fraudApplications, setFraudApplications] = useState([])
  const [fraudStats,        setFraudStats]        = useState(null)
  const [fraudPatterns,     setFraudPatterns]     = useState([])
  const [recentBlocked,     setRecentBlocked]     = useState([])
  const [selectedApp,       setSelectedApp]       = useState(null)
  const [filterLevel,       setFilterLevel]       = useState('ALL')
  const [loading,           setLoading]           = useState(true)
  const [error,             setError]             = useState(null)

  useEffect(() => {
    if (!active) return
    setLoading(true)
    setError(null)
    fetch(`${API_URL}/api/fraud`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(data => {
        setFraudApplications(data.flaggedApplications || [])
        setFraudStats(data.stats || null)
        setFraudPatterns(data.patterns || [])
        setRecentBlocked(data.recentBlocked || [])
        if (data.flaggedApplications?.length > 0) {
          setSelectedApp(data.flaggedApplications[0])
        }
      })
      .catch(err => {
        console.error('Error fetching fraud data:', err)
        setError('No se pudo cargar la información de fraude.')
      })
      .finally(() => setLoading(false))
  }, [active])

  const filteredApps = filterLevel === 'ALL'
    ? fraudApplications
    : fraudApplications.filter(app => app.riskLevel === filterLevel)

  if (loading) {
    return (
      <div className={`fraud-detection-view ${active ? 'active' : ''}`}>
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
          Cargando datos de fraude…
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`fraud-detection-view ${active ? 'active' : ''}`}>
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--error, #f87171)' }}>
          {error}
        </div>
      </div>
    )
  }

  const stats = fraudStats || {
    totalScanned: 0, highRisk: 0, mediumRisk: 0, lowRisk: 0,
    avgFraudScore: 0, blocked: 0, flaggedToday: 0,
  }

  return (
    <div className={`fraud-detection-view ${active ? 'active' : ''}`}>
      <div className="fraud-header">
        <div>
          <h1 className="fraud-title">Fraud Detection System</h1>
          <p className="fraud-subtitle">AI-powered fraud analysis and prevention</p>
        </div>
        <div className="fraud-status">
          <div className="shield-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </div>
          <div>
            <div className="fraud-status-label">System Status</div>
            <div className="fraud-status-value">ACTIVE MONITORING</div>
          </div>
        </div>
      </div>

      {/* Fraud Statistics */}
      <div className="fraud-stats-grid">
        <div className="fraud-stat-card critical">
          <div className="fraud-stat-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </div>
          <div className="fraud-stat-content">
            <div className="fraud-stat-value">{stats.highRisk}</div>
            <div className="fraud-stat-label">High Risk</div>
          </div>
        </div>
        <div className="fraud-stat-card warning">
          <div className="fraud-stat-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
          </div>
          <div className="fraud-stat-content">
            <div className="fraud-stat-value">{stats.mediumRisk}</div>
            <div className="fraud-stat-label">Medium Risk</div>
          </div>
        </div>
        <div className="fraud-stat-card safe">
          <div className="fraud-stat-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
          <div className="fraud-stat-content">
            <div className="fraud-stat-value">{stats.lowRisk}</div>
            <div className="fraud-stat-label">Low Risk</div>
          </div>
        </div>
        <div className="fraud-stat-card">
          <div className="fraud-stat-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
          </div>
          <div className="fraud-stat-content">
            <div className="fraud-stat-value">{stats.blocked}</div>
            <div className="fraud-stat-label">Blocked</div>
          </div>
        </div>
        <div className="fraud-stat-card">
          <div className="fraud-stat-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="20" x2="12" y2="10"/>
              <line x1="18" y1="20" x2="18" y2="4"/>
              <line x1="6" y1="20" x2="6" y2="16"/>
            </svg>
          </div>
          <div className="fraud-stat-content">
            <div className="fraud-stat-value">{stats.avgFraudScore}%</div>
            <div className="fraud-stat-label">Avg Score</div>
          </div>
        </div>
        <div className="fraud-stat-card">
          <div className="fraud-stat-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>
          <div className="fraud-stat-content">
            <div className="fraud-stat-value">{stats.flaggedToday}</div>
            <div className="fraud-stat-label">Flagged Today</div>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="fraud-main-grid">
        {/* Left Panel - Application List */}
        <div className="fraud-list-panel">
          <div className="fraud-list-header">
            <h3 className="fraud-list-title">Flagged Applications</h3>
            <div className="fraud-filters">
              {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(level => (
                <button
                  key={level}
                  className={`fraud-filter-btn ${filterLevel === level ? 'active' : ''}`}
                  onClick={() => setFilterLevel(level)}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>
          <div className="fraud-list">
            {filteredApps.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                Sin solicitudes en este nivel de riesgo.
              </div>
            ) : (
              filteredApps.map(app => (
                <div
                  key={app.id}
                  className={`fraud-list-item ${selectedApp?.id === app.id ? 'selected' : ''} ${app.riskLevel.toLowerCase()}`}
                  onClick={() => setSelectedApp(app)}
                >
                  <div className="fraud-item-header">
                    <span className="fraud-item-id">#{app.id}</span>
                    <span className={`fraud-risk-badge ${app.riskLevel.toLowerCase()}`}>
                      {app.riskLevel}
                    </span>
                  </div>
                  <div className="fraud-item-name">{app.name}</div>
                  <div className="fraud-item-score">
                    <span className="fraud-score-label">Fraud Score:</span>
                    <span className="fraud-score-value">{app.fraudScore}%</span>
                  </div>
                  <div className="fraud-item-time">{app.time}</div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Center Panel - Detailed Analysis */}
        {selectedApp ? (
          <div className="fraud-detail-panel">
            <div className="fraud-detail-header">
              <div>
                <h2 className="fraud-detail-name">{selectedApp.name}</h2>
                <p className="fraud-detail-id">#{selectedApp.id}</p>
              </div>
              <div className={`fraud-score-display ${selectedApp.riskLevel.toLowerCase()}`}>
                <div className="fraud-score-label-large">Fraud Score</div>
                <div className="fraud-score-value-large">{selectedApp.fraudScore}%</div>
                <div className={`fraud-risk-level ${selectedApp.riskLevel.toLowerCase()}`}>
                  {selectedApp.riskLevel} RISK
                </div>
              </div>
            </div>

            <div className="fraud-flags-section">
              <h3 className="fraud-section-title">Detection Flags</h3>
              <div className="fraud-flags-grid">
                {selectedApp.flags.map((flag, index) => (
                  <div key={index} className="fraud-flag">
                    <span className="fraud-flag-icon">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                        <line x1="12" y1="9" x2="12" y2="13"/>
                        <line x1="12" y1="17" x2="12.01" y2="17"/>
                      </svg>
                    </span>
                    {flag}
                  </div>
                ))}
              </div>
            </div>

            <div className="fraud-analysis-section">
              <h3 className="fraud-section-title">Detailed Analysis</h3>
              <div className="fraud-metrics-grid">
                <div className="fraud-metric">
                  <div className="fraud-metric-label">Identity Confidence</div>
                  <div className="fraud-metric-bar-container">
                    <div
                      className={`fraud-metric-bar ${selectedApp.details.identityConfidence > 90 ? 'safe' : selectedApp.details.identityConfidence > 70 ? 'warning' : 'critical'}`}
                      style={{ width: `${selectedApp.details.identityConfidence}%` }}
                    ></div>
                  </div>
                  <div className="fraud-metric-value">{selectedApp.details.identityConfidence}%</div>
                </div>

                <div className="fraud-metric">
                  <div className="fraud-metric-label">Document Authenticity</div>
                  <div className="fraud-metric-bar-container">
                    <div
                      className={`fraud-metric-bar ${selectedApp.details.documentAuthenticity > 90 ? 'safe' : selectedApp.details.documentAuthenticity > 70 ? 'warning' : 'critical'}`}
                      style={{ width: `${selectedApp.details.documentAuthenticity}%` }}
                    ></div>
                  </div>
                  <div className="fraud-metric-value">{selectedApp.details.documentAuthenticity}%</div>
                </div>

                <div className="fraud-metric">
                  <div className="fraud-metric-label">Behavior Score</div>
                  <div className="fraud-metric-bar-container">
                    <div
                      className={`fraud-metric-bar ${selectedApp.details.behaviorScore > 80 ? 'safe' : selectedApp.details.behaviorScore > 50 ? 'warning' : 'critical'}`}
                      style={{ width: `${selectedApp.details.behaviorScore}%` }}
                    ></div>
                  </div>
                  <div className="fraud-metric-value">{selectedApp.details.behaviorScore}%</div>
                </div>
              </div>

              <div className="fraud-checks-grid">
                <div className="fraud-check">
                  <div className="fraud-check-label">IP Reputation</div>
                  <div className={`fraud-check-value ${selectedApp.details.ipReputation === 'CLEAN' ? 'safe' : selectedApp.details.ipReputation === 'MODERATE' ? 'warning' : 'critical'}`}>
                    {selectedApp.details.ipReputation}
                  </div>
                </div>
                <div className="fraud-check">
                  <div className="fraud-check-label">Device Fingerprint</div>
                  <div className={`fraud-check-value ${selectedApp.details.deviceFingerprint === 'VERIFIED' ? 'safe' : selectedApp.details.deviceFingerprint === 'KNOWN DEVICE' ? 'warning' : 'critical'}`}>
                    {selectedApp.details.deviceFingerprint}
                  </div>
                </div>
                <div className="fraud-check">
                  <div className="fraud-check-label">Velocity Check</div>
                  <div className={`fraud-check-value ${selectedApp.details.velocityCheck === 'PASSED' ? 'safe' : selectedApp.details.velocityCheck === 'WARNING' ? 'warning' : 'critical'}`}>
                    {selectedApp.details.velocityCheck}
                  </div>
                </div>
              </div>
            </div>

            <div className="fraud-actions">
              <button className="btn btn-reject">Block Application</button>
              <button className="btn btn-secondary">Request Verification</button>
              <button className="btn btn-primary">Mark as Reviewed</button>
            </div>
          </div>
        ) : (
          <div className="fraud-detail-panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
            Selecciona una solicitud para ver el análisis.
          </div>
        )}

        {/* Right Panel - Patterns & Recent */}
        <div className="fraud-side-panel">
          <div className="fraud-patterns-section">
            <h3 className="fraud-panel-title">Fraud Patterns</h3>
            <div className="fraud-patterns-list">
              {fraudPatterns.map((pattern, index) => (
                <div key={index} className="fraud-pattern-item">
                  <div className="fraud-pattern-header">
                    <span className="fraud-pattern-name">{pattern.pattern}</span>
                    <span className={`fraud-pattern-trend ${pattern.trend}`}>
                      {pattern.trend === 'up' && (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <line x1="12" y1="19" x2="12" y2="5"/>
                          <polyline points="5 12 12 5 19 12"/>
                        </svg>
                      )}
                      {pattern.trend === 'down' && (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <line x1="12" y1="5" x2="12" y2="19"/>
                          <polyline points="19 12 12 19 5 12"/>
                        </svg>
                      )}
                      {pattern.trend === 'stable' && (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <line x1="5" y1="12" x2="19" y2="12"/>
                        </svg>
                      )}
                    </span>
                  </div>
                  <div className="fraud-pattern-count">{pattern.detected} detected</div>
                </div>
              ))}
            </div>
          </div>

          <div className="fraud-blocked-section">
            <h3 className="fraud-panel-title">Recently Blocked</h3>
            <div className="fraud-blocked-list">
              {recentBlocked.map((blocked, index) => (
                <div key={index} className="fraud-blocked-item">
                  <div className="fraud-blocked-header">
                    <span className="fraud-blocked-id">#{blocked.id}</span>
                    <span className="fraud-blocked-time">{blocked.time}</span>
                  </div>
                  <div className="fraud-blocked-reason">{blocked.reason}</div>
                  <div className="fraud-blocked-score">Score: {blocked.score}%</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default FraudDetection
