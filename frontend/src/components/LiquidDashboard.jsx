import React, { useState, useEffect } from 'react';
import './LiquidDashboard.css';
import CreditCard from './CreditCard';

const NAV_ITEMS = [
  {
    id: 'overview', label: 'Inicio',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/>
        <rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/>
      </svg>
    ),
  },
  {
    id: 'card', label: 'Mi Tarjeta',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/>
      </svg>
    ),
  },
  {
    id: 'transfers', label: 'Transferir',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4"/>
      </svg>
    ),
  },
  {
    id: 'history', label: 'Historial',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="12 8 12 12 14 14"/>
        <path d="M3.05 11a9 9 0 1 0 .5-4.5"/><polyline points="3 3 3.05 7 7.05 7"/>
      </svg>
    ),
  },
];

const TRANSACTIONS = [
  { id: 1, name: 'Liverpool',        cat: 'Compras',         date: 'Hoy 10:24',  amount: -1299, color: '#60a5fa' },
  { id: 2, name: 'Depósito Nómina',  cat: 'Ingreso',         date: 'Ayer',        amount: +4250, color: '#6ee7b7' },
  { id: 3, name: 'Netflix',          cat: 'Entretenimiento', date: 'Oct 24',      amount: -219,  color: '#a78bfa' },
  { id: 4, name: 'Starbucks',        cat: 'Restaurantes',    date: 'Oct 23',      amount: -85,   color: '#fb923c' },
  { id: 5, name: 'OXXO',            cat: 'Conveniencia',    date: 'Oct 22',      amount: -14,   color: '#94a3b8' },
];

const LiquidDashboard = ({
  active,
  userName     = '',
  creditLine   = 0,
  cardTier     = { label: 'BANCAFIEL BÁSICA', cls: 'tier-basic' },
  cardLastFour = '••••',
  cardExpiry   = '12/28',
}) => {
  const [activeNav,    setActiveNav]    = useState('overview');
  const [ringAnimated, setRingAnimated] = useState(false);

  useEffect(() => {
    if (active) {
      const t = setTimeout(() => setRingAnimated(true), 500);
      return () => clearTimeout(t);
    }
  }, [active]);

  if (!active) return null;

  const amount       = Math.round(parseFloat(creditLine));
  const usedAmount   = 0;
  const availableAmt = amount - usedAmount;
  const usedPct      = amount > 0 ? (usedAmount / amount) * 100 : 0;
  const availPct     = 100 - usedPct;

  const firstName   = userName ? userName.split(' ')[0] : 'Cliente';
  const displayName = userName ? userName.toUpperCase() : 'CLIENTE';
  const tierLabel   = cardTier.label.replace('BANCAFIEL ', '');
  const cardType    = cardTier.cls === 'tier-gold'    ? 'gold-dark'
                    : cardTier.cls === 'tier-classic' ? 'blue-dark'
                    : 'gray-dark';

  const cardGlow = cardTier.cls === 'tier-gold'    ? 'rgba(251,191,36,0.25)'
                 : cardTier.cls === 'tier-classic' ? 'rgba(96,165,250,0.25)'
                 : 'rgba(148,163,184,0.12)';

  // SVG ring
  const R    = 48;
  const SW   = 6;
  const r    = R - SW / 2;
  const circ = 2 * Math.PI * r;
  const ringOffset = ringAnimated ? circ - (availPct / 100) * circ : circ;

  const now      = new Date();
  const cutoff   = new Date(now.getFullYear(), now.getMonth() + 1, 25);
  const cutoffFmt = cutoff.toLocaleDateString('es-MX', { day: 'numeric', month: 'long' });

  return (
    <div className="lbd-root">
      <div className="lbd-shell">

        {/* ── NAV ── */}
        <nav className="lbd-nav glass-panel">
          <div className="lbd-nav-logo">
            <div className="logo-orb" style={{ width: 28, height: 28 }} />
          </div>

          <div className="lbd-nav-items">
            {NAV_ITEMS.map(n => (
              <button
                key={n.id}
                className={`lbd-nav-btn ${activeNav === n.id ? 'lbd-nav-btn--active' : ''}`}
                onClick={() => setActiveNav(n.id)}
                title={n.label}
              >
                {n.icon}
              </button>
            ))}
          </div>

          <div className="lbd-nav-avatar">
            {firstName[0]?.toUpperCase()}
          </div>
        </nav>

        {/* ── CONTENT ── */}
        <div className="lbd-content">

          {/* Header */}
          <header className="lbd-header">
            <div className="lbd-header-left">
              <div className="logo-mark chrome-text" style={{ fontSize: '20px' }}>
                BANCAFIEL
              </div>
            </div>
            <div className="user-pill">
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{displayName}</span>
              <div className="avatar" />
            </div>
          </header>

          {/* Body grid — 2×2 */}
          <div className="lbd-body">

            {/* TOP-LEFT: Hero / Credit */}
            <section className="glass-panel lbd-hero" style={{ '--delay': '0.05s' }}>
              <div className="lbd-hero-inner">
                <div className="lbd-hero-left">
                  <p className="lbd-label">CRÉDITO DISPONIBLE</p>
                  <div className="lbd-big-number chrome-text">
                    <span className="lbd-big-currency">$</span>
                    {availableAmt.toLocaleString('en-US')}
                  </div>
                  <span className={`credit-tier ${cardTier.cls}`} style={{ alignSelf: 'flex-start' }}>
                    {tierLabel}
                  </span>

                  <div className="lbd-stats-row">
                    <div className="lbd-stat">
                      <span className="lbd-stat-label">Límite</span>
                      <span className="lbd-stat-val">${amount.toLocaleString('en-US')}</span>
                    </div>
                    <div className="lbd-stat-div" />
                    <div className="lbd-stat">
                      <span className="lbd-stat-label">Utilizado</span>
                      <span className="lbd-stat-val" style={{ color: '#f87171' }}>${usedAmount.toLocaleString('en-US')}</span>
                    </div>
                    <div className="lbd-stat-div" />
                    <div className="lbd-stat">
                      <span className="lbd-stat-label">Disponible</span>
                      <span className="lbd-stat-val" style={{ color: '#6ee7b7' }}>${availableAmt.toLocaleString('en-US')}</span>
                    </div>
                  </div>
                </div>

                {/* Ring */}
                <div className="lbd-ring-wrap">
                  <svg width={R * 2} height={R * 2} viewBox={`0 0 ${R * 2} ${R * 2}`} style={{ overflow: 'visible' }}>
                    <circle cx={R} cy={R} r={r} fill="none"
                      stroke="rgba(255,255,255,0.08)" strokeWidth={SW} />
                    <circle cx={R} cy={R} r={r} fill="none"
                      stroke="rgba(255,255,255,0.88)" strokeWidth={SW}
                      strokeLinecap="round"
                      strokeDasharray={circ}
                      strokeDashoffset={ringOffset}
                      transform={`rotate(-90 ${R} ${R})`}
                      style={{ transition: 'stroke-dashoffset 1.4s cubic-bezier(0.23,1,0.32,1)', filter: 'drop-shadow(0 0 8px rgba(255,255,255,0.25))' }}
                    />
                  </svg>
                  <div className="lbd-ring-center">
                    <span className="lbd-ring-pct">{availPct.toFixed(0)}%</span>
                    <span className="lbd-ring-sub">libre</span>
                  </div>
                </div>
              </div>

              {/* Util bar */}
              <div className="lbd-util-wrap">
                <div className="lbd-util-track">
                  <div className="lbd-util-fill" style={{ width: `${Math.max(usedPct, 0.3)}%` }} />
                </div>
                <div className="lbd-util-labels">
                  <span>{usedPct.toFixed(0)}% utilizado</span>
                  <span>{availPct.toFixed(0)}% disponible</span>
                </div>
              </div>
            </section>

            {/* TOP-RIGHT: Card standalone (no container) */}
            <div className="lbd-card-standalone" style={{ '--delay': '0.09s', '--card-glow': cardGlow }}>
              <div className="lbd-card-wrap" style={{ '--glow': cardGlow }}>
                <CreditCard
                  type={cardType}
                  tier={tierLabel}
                  number="•••• •••• •••• ••••"
                  expiry={cardExpiry}
                  holder={displayName}
                />
              </div>
            </div>

            {/* BOTTOM-LEFT: Transactions */}
            <section className="glass-panel lbd-txn-panel" style={{ '--delay': '0.12s' }}>
              <div className="lbd-panel-head">
                <span className="lbd-panel-title">Movimientos Recientes</span>
                <button className="auth-back-link" style={{ fontSize: '12px', marginTop: 0, opacity: 0.5 }}>
                  Ver todos →
                </button>
              </div>
              <div className="lbd-txn-list">
                {TRANSACTIONS.map((t, i) => (
                  <div key={t.id} className="lbd-txn" style={{ '--ti': i, '--cc': t.color }}>
                    <div className="lbd-txn-dot" />
                    <div className="lbd-txn-info">
                      <span className="lbd-txn-name">{t.name}</span>
                      <span className="lbd-txn-meta">
                        <span style={{ color: t.color }}>{t.cat}</span>
                        {' · '}{t.date}
                      </span>
                    </div>
                    <span className={`lbd-txn-amt ${t.amount > 0 ? 'lbd-pos' : ''}`}>
                      {t.amount > 0 ? '+' : ''}${Math.abs(t.amount).toLocaleString('en-US')}
                    </span>
                  </div>
                ))}
              </div>
            </section>

            {/* BOTTOM-RIGHT: Account */}
            <div className="glass-panel lbd-account-panel" style={{ '--delay': '0.16s' }}>
              <span className="lbd-panel-title" style={{ display: 'block', marginBottom: '18px' }}>
                Estado de Cuenta
              </span>
              <div className="credit-details" style={{ marginBottom: '20px' }}>
                {[
                  { label: 'Saldo actual',       val: '$0.00',    hi: false },
                  { label: 'Pago mínimo',         val: '$0.00',    hi: false },
                  { label: 'Próximo corte',       val: cutoffFmt,  hi: false },
                  { label: 'Sin intereses hasta', val: cutoffFmt,  hi: true  },
                ].map(row => (
                  <div key={row.label} className="credit-detail-row">
                    <span>{row.label}</span>
                    <span className="detail-val" style={row.hi ? { color: '#6ee7b7' } : {}}>
                      {row.val}
                    </span>
                  </div>
                ))}
              </div>
              <button className="liquid-btn">Realizar Pago</button>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

export default LiquidDashboard;
