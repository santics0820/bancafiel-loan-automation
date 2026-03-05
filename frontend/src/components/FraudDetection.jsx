import { useState, useEffect } from 'react'
import { API_URL } from '../config'

const riskColors = {
  HIGH:   '#f87171',
  MEDIUM: '#fbbf24',
  LOW:    '#6ee7b7',
}

const statusLabel = {
  processing: 'Pendiente',
  approved:   'Aprobada',
  rejected:   'Rechazada',
}

const statusColors = {
  processing: '#fbbf24',
  approved:   '#6ee7b7',
  rejected:   '#f87171',
}

function FraudDetection({ active }) {
  const [data,       setData]       = useState(null)
  const [selected,   setSelected]   = useState(null)
  const [filter,     setFilter]     = useState('ALL')
  const [loading,    setLoading]    = useState(true)
  const [error,      setError]      = useState(null)

  useEffect(() => {
    if (!active) return
    setLoading(true)
    setError(null)
    fetch(`${API_URL}/api/fraud`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(d => {
        setData(d)
        const flagged = d.flaggedApplications ?? []
        setSelected(flagged[0] ?? null)
        setLoading(false)
      })
      .catch(err => { console.error(err); setError(true); setLoading(false) })
  }, [active])

  if (!active) return null

  if (loading) return (
    <div className="workspace" style={{ alignItems: 'center', justifyContent: 'center' }}>
      <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Cargando datos de fraude…</p>
    </div>
  )

  if (error) return (
    <div className="workspace" style={{ alignItems: 'center', justifyContent: 'center' }}>
      <p style={{ color: '#f87171', fontSize: '13px' }}>No se pudo cargar la información de fraude.</p>
    </div>
  )

  const stats    = data?.stats ?? {}
  const patterns = data?.patterns ?? []
  const blocked  = data?.recentBlocked ?? []
  const flagged  = (data?.flaggedApplications ?? []).filter(a =>
    filter === 'ALL' || a.riskLevel === filter
  )

  return (
    <div className="workspace" style={{ overflow: 'auto', padding: '24px', gap: '20px', flexDirection: 'column' }}>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '12px' }}>
        {[
          { label: 'Escaneadas',    value: stats.totalScanned ?? 0,   color: 'var(--text-primary)' },
          { label: 'Riesgo Alto',   value: stats.highRisk ?? 0,       color: '#f87171' },
          { label: 'Riesgo Medio',  value: stats.mediumRisk ?? 0,     color: '#fbbf24' },
          { label: 'Riesgo Bajo',   value: stats.lowRisk ?? 0,        color: '#6ee7b7' },
          { label: 'Score Promedio',value: `${stats.avgFraudScore ?? 0}%`, color: 'var(--text-primary)' },
          { label: 'Hoy',           value: stats.flaggedToday ?? 0,   color: 'var(--accent-blue)' },
        ].map(s => (
          <div key={s.label} className="glass-panel" style={{ padding: '16px', textAlign: 'center' }}>
            <div style={{ fontSize: '24px', fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Main content */}
      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr 240px', gap: '16px', minHeight: 0 }}>

        {/* Left — flagged list */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: '16px 16px 8px', borderBottom: '1px solid var(--glass-border)' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, letterSpacing: '0.08em', color: 'var(--text-secondary)', marginBottom: '10px' }}>SOLICITUDES MARCADAS</div>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {['ALL', 'HIGH', 'MEDIUM'].map(f => (
                <span
                  key={f}
                  onClick={() => setFilter(f)}
                  className="filter-chip"
                  style={filter === f ? { color: riskColors[f] ?? 'var(--text-primary)', borderColor: riskColors[f] ?? 'var(--text-primary)', background: 'rgba(255,255,255,0.1)' } : {}}
                >
                  {f === 'ALL' ? 'Todas' : f === 'HIGH' ? 'Alto' : 'Medio'}
                </span>
              ))}
            </div>
          </div>
          <div style={{ overflowY: 'auto', flex: 1 }}>
            {flagged.length === 0 && (
              <p style={{ padding: '20px', color: 'var(--text-secondary)', fontSize: '13px', textAlign: 'center' }}>Sin solicitudes marcadas.</p>
            )}
            {flagged.map(app => (
              <div
                key={app.applicationId}
                className={`app-item ${selected?.applicationId === app.applicationId ? 'selected' : ''}`}
                onClick={() => setSelected(app)}
              >
                <div className="app-meta">
                  <span>#{app.id}</span>
                  <span>{app.time}</span>
                </div>
                <div className="app-name">{app.name}</div>
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center', marginTop: '4px' }}>
                  <span className="risk-pill" style={{ color: riskColors[app.riskLevel], borderColor: riskColors[app.riskLevel] }}>
                    {app.riskLevel === 'HIGH' ? 'Alto' : 'Medio'} · {app.fraudScore}%
                  </span>
                  <span style={{ fontSize: '10px', color: statusColors[app.status], textTransform: 'uppercase' }}>
                    {statusLabel[app.status] ?? app.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Center — detail */}
        {selected ? (
          <div className="glass-panel" style={{ padding: '24px', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
              <div>
                <h2 className="chrome-text" style={{ fontSize: '20px', margin: 0 }}>{selected.name}</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '13px', margin: '4px 0 0' }}>#{selected.id} · ${selected.loanAmount?.toLocaleString('es-MX')} MXN</p>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '32px', fontWeight: 800, color: riskColors[selected.riskLevel] }}>{selected.fraudScore}%</div>
                <div style={{ fontSize: '11px', color: riskColors[selected.riskLevel], letterSpacing: '0.08em', fontWeight: 700 }}>{selected.riskLevel === 'HIGH' ? 'ALTO RIESGO' : 'RIESGO MEDIO'}</div>
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <div className="card-title-sm" style={{ marginBottom: '12px' }}>Alertas Detectadas</div>
              {selected.flags.length === 0 ? (
                <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Sin alertas específicas.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {selected.flags.map((flag, i) => (
                    <div key={i} className="glass-panel" style={{ padding: '10px 14px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ color: riskColors[selected.riskLevel], fontSize: '16px' }}>⚠</span>
                      <span style={{ fontSize: '13px', color: 'var(--text-primary)' }}>{flag}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div>
              <div className="card-title-sm" style={{ marginBottom: '12px' }}>Información</div>
              <div className="data-grid-3">
                <div className="data-cell">
                  <div className="data-label">Folio</div>
                  <div className="data-value">#{selected.id}</div>
                </div>
                <div className="data-cell">
                  <div className="data-label">Score Fraude</div>
                  <div className="data-value" style={{ color: riskColors[selected.riskLevel] }}>{selected.fraudScore}%</div>
                </div>
                <div className="data-cell">
                  <div className="data-label">Estado</div>
                  <div className="data-value" style={{ color: statusColors[selected.status] }}>{statusLabel[selected.status] ?? selected.status}</div>
                </div>
                <div className="data-cell">
                  <div className="data-label">Monto</div>
                  <div className="data-value">${selected.loanAmount?.toLocaleString('es-MX')} MXN</div>
                </div>
                <div className="data-cell">
                  <div className="data-label">Riesgo</div>
                  <div className="data-value" style={{ color: riskColors[selected.riskLevel] }}>{selected.riskLevel === 'HIGH' ? 'Alto' : 'Medio'}</div>
                </div>
                <div className="data-cell">
                  <div className="data-label">Revisado</div>
                  <div className="data-value">{selected.time}</div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="glass-panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', fontSize: '13px' }}>
            Selecciona una solicitud para ver el detalle.
          </div>
        )}

        {/* Right — patterns + recently blocked */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
          <div className="glass-panel" style={{ padding: '16px' }}>
            <div className="card-title-sm" style={{ marginBottom: '12px' }}>Reglas más frecuentes</div>
            {patterns.length === 0 ? (
              <p style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>Sin datos aún.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {patterns.map((p, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)', flex: 1, marginRight: '8px' }}>{p.pattern}</span>
                    <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', background: 'rgba(255,255,255,0.08)', padding: '2px 8px', borderRadius: '100px' }}>{p.detected}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="glass-panel" style={{ padding: '16px' }}>
            <div className="card-title-sm" style={{ marginBottom: '12px' }}>Rechazadas (Alto Riesgo)</div>
            {blocked.length === 0 ? (
              <p style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>Ninguna aún.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {blocked.map((b, i) => (
                  <div key={i} style={{ borderBottom: '1px solid var(--glass-border)', paddingBottom: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '12px', fontWeight: 700, color: '#f87171' }}>#{b.id}</span>
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{b.time}</span>
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>{b.name}</div>
                    <div style={{ fontSize: '11px', color: '#f87171', marginTop: '2px' }}>Score: {b.score}%</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default FraudDetection
