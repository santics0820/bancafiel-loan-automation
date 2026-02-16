import { useState } from 'react'
import './Overview.css'

const statsData = {
  totalApplications: 147,
  pendingReview: 12,
  approved: 98,
  rejected: 37,
  avgProcessingTime: '2.4 HRS',
  successRate: '72.6%',
  todayProcessed: 8,
  avgFraudScore: '2.1%'
}

const recentActivity = [
  { id: 'LN-2024-8821', name: 'Elena Rodriguez', action: 'Pending Review', time: '10m ago', status: 'warning' },
  { id: 'LN-2024-8820', name: 'Carlos Mendez', action: 'Approved', time: '25m ago', status: 'success' },
  { id: 'LN-2024-8819', name: 'Marco Silva', action: 'Documents Processed', time: '45m ago', status: 'processing' },
  { id: 'LN-2024-8818', name: 'Ana Lopez', action: 'Fraud Check Complete', time: '1h ago', status: 'processing' },
  { id: 'LN-2024-8817', name: 'Juan Garcia', action: 'Rejected', time: '2h ago', status: 'error' },
  { id: 'LN-2024-8816', name: 'Maria Santos', action: 'Approved', time: '3h ago', status: 'success' }
]

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

const applicationsByStatus = [
  { status: 'Processing', count: 12, percentage: 8.2 },
  { status: 'Pending Review', count: 15, percentage: 10.2 },
  { status: 'Approved', count: 98, percentage: 66.7 },
  { status: 'Rejected', count: 22, percentage: 15.0 }
]

function Overview({ active }) {
  const [selectedWorkflow, setSelectedWorkflow] = useState(null)

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

      {/* Statistics Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Applications</div>
          <div className="stat-value">{statsData.totalApplications}</div>
          <div className="stat-change positive">+12 THIS WEEK</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Pending Review</div>
          <div className="stat-value warning">{statsData.pendingReview}</div>
          <div className="stat-change">AWAITING ANALYST</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Approved</div>
          <div className="stat-value success">{statsData.approved}</div>
          <div className="stat-change positive">+5 TODAY</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Rejected</div>
          <div className="stat-value error">{statsData.rejected}</div>
          <div className="stat-change">25.2% RATE</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Avg Processing Time</div>
          <div className="stat-value">{statsData.avgProcessingTime}</div>
          <div className="stat-change positive">-0.3H FROM AVG</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Success Rate</div>
          <div className="stat-value success">{statsData.successRate}</div>
          <div className="stat-change positive">+2.1% THIS MONTH</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Processed Today</div>
          <div className="stat-value">{statsData.todayProcessed}</div>
          <div className="stat-change">5 PENDING</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Avg Fraud Score</div>
          <div className="stat-value success">{statsData.avgFraudScore}</div>
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
            <span className="panel-badge">147 TOTAL</span>
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
    </div>
  )
}

export default Overview
