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
      identityMatch: '99.8% VERIFIED',
      incomeVerification: 'INCONSISTENT',
      fraudProbability: '1.2% (LOW)',
      aiAnalysis: 'The declared monthly income ($45,000) varies by 15% from the average deposits found in the uploaded bank statements ($38,200). Manual review recommended.',
      employment: 'FULL-TIME',
      employer: 'TECH SOLUTIONS INC.',
      tenure: '3 YRS, 2 MOS',
      monthlyRent: '$12,500 MXN',
      requestedAmount: '$250,000 MXN',
      term: '48 MONTHS'
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
      identityMatch: '99.9% VERIFIED',
      incomeVerification: 'VERIFIED',
      fraudProbability: '0.5% (LOW)',
      aiAnalysis: 'All documentation verified successfully. Income matches bank statements. No red flags detected.',
      employment: 'FULL-TIME',
      employer: 'CONSULTING FIRM SA',
      tenure: '5 YRS, 8 MOS',
      monthlyRent: '$15,000 MXN',
      requestedAmount: '$180,000 MXN',
      term: '36 MONTHS'
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
      identityMatch: '95.2% VERIFIED',
      incomeVerification: 'INCONSISTENT',
      fraudProbability: '8.7% (HIGH)',
      aiAnalysis: 'Multiple inconsistencies detected. Income verification failed. Address mismatch between documents. Recommend thorough manual review.',
      employment: 'SELF-EMPLOYED',
      employer: 'INDEPENDENT CONTRACTOR',
      tenure: '1 YR, 3 MOS',
      monthlyRent: '$8,000 MXN',
      requestedAmount: '$300,000 MXN',
      term: '60 MONTHS'
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
      identityMatch: '99.5% VERIFIED',
      incomeVerification: 'VERIFIED',
      fraudProbability: '0.8% (LOW)',
      aiAnalysis: 'Strong application with consistent documentation. Income verified against multiple sources.',
      employment: 'FULL-TIME',
      employer: 'FINANCIAL SERVICES CO.',
      tenure: '4 YRS, 1 MO',
      monthlyRent: '$14,000 MXN',
      requestedAmount: '$200,000 MXN',
      term: '42 MONTHS'
    }
  }
]

function AnalystDashboard({ active }) {
  const [selectedApp, setSelectedApp] = useState(applications[0])
  const [currentView, setCurrentView] = useState('applications')

  return (
    <div className={`app-view dashboard-view ${active ? 'active' : ''}`}>
      <nav className="dash-nav">
        <div style={{ display: 'flex', alignItems: 'center', gap: '60px', height: '100%' }}>
          <Logo style={{ color: '#FFFFFF' }} />
          <div className="nav-links">
            <a
              href="#"
              className={`nav-link ${currentView === 'overview' ? 'active' : ''}`}
              onClick={(e) => { e.preventDefault(); setCurrentView('overview'); }}
            >
              Overview
            </a>
            <a
              href="#"
              className={`nav-link ${currentView === 'applications' ? 'active' : ''}`}
              onClick={(e) => { e.preventDefault(); setCurrentView('applications'); }}
            >
              Applications (12)
            </a>
            <a
              href="#"
              className={`nav-link ${currentView === 'fraud' ? 'active' : ''}`}
              onClick={(e) => { e.preventDefault(); setCurrentView('fraud'); }}
            >
              Fraud Detection
            </a>
            <a href="#" className="nav-link">Settings</a>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '40px', height: '40px', background: '#FFFFFF', borderRadius: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, color: 'var(--brand-blue)', fontSize: '0.9rem' }}>
            JD
          </div>
        </div>
      </nav>

      <Overview active={currentView === 'overview'} />
      <FraudDetection active={currentView === 'fraud'} />

      <div className={`workspace grid-pattern ${currentView === 'applications' ? '' : 'hidden'}`}>
        <div className="list-panel">
          <div className="list-header">
            <input type="text" className="search-bar" placeholder="SEARCH APPLICATION ID..." />
            <div style={{ display: 'flex', gap: '8px', marginTop: '16px', alignItems: 'center' }}>
              <span className="text-caps" style={{ color: 'rgba(255,255,255,0.6)' }}>Filter:</span>
              <span className="text-caps" style={{ color: '#FFFFFF', background: 'rgba(255,255,255,0.2)', padding: '4px 8px', cursor: 'pointer' }}>
                Pending
              </span>
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
                <span className={`risk-pill risk-${app.risk}`}>Risk: {app.risk === 'med' ? 'Medium' : app.risk === 'low' ? 'Low' : 'High'}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="detail-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '40px', position: 'relative', zIndex: 1 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '12px' }}>
                <h2>{selectedApp.name}</h2>
                <span className={`risk-pill risk-${selectedApp.risk}`} style={{ fontSize: '0.9rem', padding: '6px 16px', background: 'rgba(255,255,255,0.1)' }}>
                  {selectedApp.risk === 'med' ? 'Medium' : selectedApp.risk === 'low' ? 'Low' : 'High'} Risk Level
                </span>
              </div>
              <p style={{ color: 'rgba(255,255,255,0.6)', fontFamily: 'var(--font-mono)', fontSize: '1.1rem' }}>
                APPLICATION ID: {selectedApp.applicationId}
              </p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div className="text-caps" style={{ color: 'rgba(255,255,255,0.6)', marginBottom: '4px' }}>Credit Score</div>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: '#FFFFFF', lineHeight: 1 }}>{selectedApp.creditScore}</div>
            </div>
          </div>

          <div className="detail-card">
            <div className="card-header">
              <span className="text-caps" style={{ color: '#FFFFFF', fontSize: '0.9rem' }}>AI Validation Engine</span>
              <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)', fontFamily: 'var(--font-mono)' }}>PROCESSED IN 1.2S</span>
            </div>
            <div className="data-grid">
              <div className="data-cell">
                <div className="data-label">Identity Match</div>
                <div className="data-value" style={{ color: '#4ADE80' }}>{selectedApp.details.identityMatch}</div>
              </div>
              <div className="data-cell">
                <div className="data-label">Income Verification</div>
                <div className="data-value" style={{ color: selectedApp.details.incomeVerification === 'VERIFIED' ? '#4ADE80' : '#FFC107' }}>
                  {selectedApp.details.incomeVerification}
                </div>
              </div>
              <div className="data-cell">
                <div className="data-label">Fraud Probability</div>
                <div className="data-value">{selectedApp.details.fraudProbability}</div>
              </div>
            </div>
            <div className="ai-analysis">
              <div className="ai-row">
                <div className="ai-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                  </svg>
                </div>
                <div style={{ fontSize: '0.95rem', lineHeight: 1.6, color: '#FFFFFF' }}>
                  <strong style={{ textTransform: 'uppercase' }}>
                    {selectedApp.details.incomeVerification === 'VERIFIED' ? 'Verification Complete:' : 'Income Discrepancy Detected:'}
                  </strong> {selectedApp.details.aiAnalysis}
                </div>
              </div>
            </div>
          </div>

          <div className="detail-card">
            <div className="card-header">
              <span className="card-title">Financial Profile</span>
            </div>
            <div className="data-grid">
              <div className="data-cell">
                <div className="data-label">Employment</div>
                <div className="data-value">{selectedApp.details.employment}</div>
              </div>
              <div className="data-cell">
                <div className="data-label">Employer</div>
                <div className="data-value">{selectedApp.details.employer}</div>
              </div>
              <div className="data-cell">
                <div className="data-label">Tenure</div>
                <div className="data-value">{selectedApp.details.tenure}</div>
              </div>
              <div className="data-cell">
                <div className="data-label">Monthly Rent/Mortgage</div>
                <div className="data-value">{selectedApp.details.monthlyRent}</div>
              </div>
              <div className="data-cell">
                <div className="data-label">Requested Amount</div>
                <div className="data-value">{selectedApp.details.requestedAmount}</div>
              </div>
              <div className="data-cell">
                <div className="data-label">Term</div>
                <div className="data-value">{selectedApp.details.term}</div>
              </div>
            </div>
          </div>

          <div className="action-bar">
            <button className="btn btn-reject">Reject Application</button>
            <button className="btn btn-secondary">Request More Info</button>
            <button className="btn btn-primary">Approve Loan</button>
          </div>

          <div style={{ height: '60px' }}></div>
        </div>
      </div>
    </div>
  )
}

export default AnalystDashboard
