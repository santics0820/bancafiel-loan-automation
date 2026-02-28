import React from 'react';
import './LiquidDashboard.css';

const LiquidDashboard = ({ active }) => {
  if (!active) return null;

  return (
    <div className="liquid-banking-root">
      <div className="ambient-light"></div>
      <div className="ambient-reflection"></div>

      <div className="dashboard-container">
          
          <nav className="nav-rail glass-panel">
              <div className="nav-item active">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="3" width="7" height="7" rx="2"></rect>
                      <rect x="14" y="3" width="7" height="7" rx="2"></rect>
                      <rect x="14" y="14" width="7" height="7" rx="2"></rect>
                      <rect x="3" y="14" width="7" height="7" rx="2"></rect>
                  </svg>
              </div>
              <div className="nav-item">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 12V7H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
                      <path d="M3 5v14a2 2 0 0 0 2 2h16v-5"></path>
                      <path d="M18 12a2 2 0 0 0 0 4h4v-4Z"></path>
                  </svg>
              </div>
              <div className="nav-item">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                      <polyline points="7 10 12 15 17 10"></polyline>
                      <line x1="12" y1="15" x2="12" y2="3"></line>
                  </svg>
              </div>
              <div className="nav-item" style={{ marginTop: 'auto' }}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.1a2 2 0 0 1-1-1.72v-.51a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                  </svg>
              </div>
          </nav>

          <header className="header-area">
              <div className="logo-mark chrome-text">
                  <div className="logo-orb"></div>
                  AETHER BANK
              </div>
              <div className="user-pill">
                  <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Private Client</span>
                  <div className="avatar"></div>
              </div>
          </header>

          <main className="main-content">
              
              <section className="glass-panel hero-card">
                  <div>
                      <div className="balance-label">Total Asset Value</div>
                      <div className="balance-amount chrome-text">
                          <span className="currency">$</span>124,592.40
                      </div>
                      <div style={{ display: 'flex', gap: '8px' }}>
                           <span style={{ color: '#6ee7b7', fontSize: '14px', background: 'rgba(110,231,183,0.1)', padding: '4px 8px', borderRadius: '4px' }}>+2.4%</span>
                           <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>vs last month</span>
                      </div>
                  </div>

                  <div className="chart-container">
                      <svg width="100%" height="100%" preserveAspectRatio="none" viewBox="0 0 800 120">
                          <defs>
                              <linearGradient id="liquidGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                  <stop offset="0%" style={{ stopColor: '#94a3b8', stopOpacity: 0.4 }}></stop>
                                  <stop offset="50%" style={{ stopColor: '#ffffff', stopOpacity: 1 }}></stop>
                                  <stop offset="100%" style={{ stopColor: '#94a3b8', stopOpacity: 0.4 }}></stop>
                              </linearGradient>
                              <linearGradient id="fillGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                  <stop offset="0%" style={{ stopColor: '#ffffff', stopOpacity: 0.5 }}></stop>
                                  <stop offset="100%" style={{ stopColor: '#ffffff', stopOpacity: 0 }}></stop>
                              </linearGradient>
                          </defs>
                          <path className="chart-fill" d="M0,80 C150,80 200,30 350,50 C500,70 600,10 800,40 V120 H0 Z"></path>
                          <path className="chart-line" d="M0,80 C150,80 200,30 350,50 C500,70 600,10 800,40"></path>
                      </svg>
                  </div>
              </section>

              <section className="glass-panel transactions-card">
                  <div className="section-header">
                      <div className="section-title">Latest Activity</div>
                      <div style={{ color: 'var(--text-secondary)', fontSize: '13px', cursor: 'pointer' }}>View All</div>
                  </div>
                  
                  <div className="transaction-list">
                      <div className="transaction-item">
                          <div className="t-icon">
                              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
                          </div>
                          <div className="t-info">
                              <div className="t-name">Apple Store</div>
                              <div className="t-date">Today, 10:24 AM</div>
                          </div>
                          <div className="t-amount negative">-$1,299.00</div>
                      </div>

                      <div className="transaction-item">
                          <div className="t-icon">
                              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                          </div>
                          <div className="t-info">
                              <div className="t-name">Salary Deposit</div>
                              <div className="t-date">Yesterday</div>
                          </div>
                          <div className="t-amount positive">+$4,250.00</div>
                      </div>

                      <div className="transaction-item">
                          <div className="t-icon">
                              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg>
                          </div>
                          <div className="t-info">
                              <div className="t-name">Subscription</div>
                              <div className="t-date">Oct 24</div>
                          </div>
                          <div className="t-amount negative">-$14.00</div>
                      </div>
                  </div>
              </section>
          </main>

          <aside className="sidebar-right">
              
              <div className="glass-panel card-visual">
                  <div className="card-chip"></div>
                  <div className="card-number">
                      •••• •••• •••• 8842
                  </div>
                  <div className="card-details">
                      <span>ALEX MORGAN</span>
                      <span>12/26</span>
                  </div>
              </div>

              <div className="glass-panel transfer-panel">
                  <div className="section-header">
                      <div className="section-title" style={{ fontSize: '16px' }}>Quick Transfer</div>
                  </div>
                  <div className="contacts-grid">
                      <div className="contact-bubble">
                          <div className="contact-img" style={{ background: '#475569' }}></div>
                          <div className="contact-name">Sarah</div>
                      </div>
                      <div className="contact-bubble">
                          <div className="contact-img" style={{ background: '#52525b' }}></div>
                          <div className="contact-name">Mike</div>
                      </div>
                      <div className="contact-bubble">
                          <div className="contact-img" style={{ background: '#3f3f46' }}></div>
                          <div className="contact-name">Anna</div>
                      </div>
                      <div className="contact-bubble">
                          <div className="contact-img" style={{ background: '#27272a' }}></div>
                          <div className="contact-name">Tom</div>
                      </div>
                      <div className="contact-bubble" style={{ border: '1px dashed rgba(255,255,255,0.3)' }}>
                          <svg width="20" height="20" stroke="white" strokeWidth="2"><line x1="10" y1="4" x2="10" y2="16"></line><line x1="4" y1="10" x2="16" y2="10"></line></svg>
                      </div>
                  </div>
                  <button className="liquid-btn">Send Money</button>
              </div>
          </aside>

      </div>
    </div>
  );
};

export default LiquidDashboard;
