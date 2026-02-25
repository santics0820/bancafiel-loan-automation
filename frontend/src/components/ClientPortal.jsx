import { useState } from 'react'
import './ClientPortal.css'
import Logo from './Logo'
import INEScanner from './INEScanner'

function ClientPortal({ active }) {
  const [showScanner, setShowScanner]       = useState(false)
  const [capturedINEFront, setCapturedINEFront] = useState(null)
  const [capturedINEBack, setCapturedINEBack]   = useState(null)
  const [capturedFace, setCapturedFace]         = useState(null)

  const handleCapture = (image, mode) => {
    if (mode === 'card-front') {
      setCapturedINEFront(image)
    } else if (mode === 'card-back') {
      setCapturedINEBack(image)
    } else if (mode === 'face') {
      setCapturedFace(image)
      setShowScanner(false) // cierra al completar el último paso
    }
  }

  return (
    <div className={`app-view client-view ${active ? 'active' : ''}`}>
      <div className={`portal-card ${showScanner ? 'scanner-mode' : ''}`}>
        {showScanner ? (
          <div className="scanner-view">
            <INEScanner onCapture={handleCapture} onBack={() => setShowScanner(false)} />
          </div>
        ) : (
          <>
            <div className="portal-header">
              <Logo className="portal-title" />
              <h1 style={{ fontSize: '2.5rem', fontWeight: 900, marginTop: '24px', lineHeight: 0.9, textTransform: 'uppercase' }}>
                Secure Document Portal
              </h1>
              <p style={{ color: 'rgba(255,255,255,0.7)', marginTop: '16px', lineHeight: 1.5, fontSize: '1.1rem', maxWidth: '90%' }}>
                Please upload the required documents to finalize your loan application.
              </p>
            </div>
            <div className="portal-body">
              <div className="doc-list">
                <div className="doc-item">
                  <span style={{ fontWeight: 700, textTransform: 'uppercase' }}>Proof of Address</span>
                  <div className="doc-status checked"></div>
                </div>
                
                <div className="doc-item" onClick={() => setShowScanner(true)} style={{ cursor: 'pointer', border: (capturedINEFront && capturedINEBack && capturedFace) ? '1px solid #4CAF50' : '1px solid rgba(255,255,255,0.2)' }}>
                  <span style={{ fontWeight: 700, textTransform: 'uppercase' }}>ID & Face Verification</span>
                  {(capturedINEFront && capturedINEBack && capturedFace) ? (
                    <div className="doc-status checked"></div>
                  ) : (
                    <div style={{ display: 'flex', gap: '5px' }}>
                      {(!capturedINEFront || !capturedINEBack) && <span style={{ fontSize: '0.65rem', color: '#e91e63', textTransform: 'uppercase', fontWeight: 700, padding: '2px 4px', border: '1px solid #e91e63' }}>INE Pending</span>}
                      {!capturedFace && <span style={{ fontSize: '0.65rem', color: '#e91e63', textTransform: 'uppercase', fontWeight: 700, padding: '2px 4px', border: '1px solid #e91e63' }}>Face Pending</span>}
                    </div>
                  )}
                </div>

                <div className="doc-item" style={{ borderStyle: 'dashed', borderColor: '#FFFFFF', background: 'rgba(255,255,255,0.1)' }}>
                  <span style={{ fontWeight: 700, color: '#FFFFFF', textTransform: 'uppercase' }}>Bank Statement (3mo)</span>
                  <span style={{ fontSize: '0.75rem', color: '#FFFFFF', textTransform: 'uppercase', fontWeight: 700, padding: '2px 6px', border: '1px solid white' }}>
                    Pending
                  </span>
                </div>
              </div>

              <div className="upload-zone">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="17 8 12 3 7 8"></polyline>
                  <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
                <h3 style={{ fontSize: '1.25rem', marginBottom: '8px', textTransform: 'uppercase', fontWeight: 800 }}>
                  Drag & Drop Bank Statement
                </h3>
                <p style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.6)', fontFamily: 'var(--font-mono)' }}>
                  PDF or JPG, max 10MB
                </p>
              </div>

              <button className="btn btn-primary" style={{ width: '100%' }}>
                SUBMIT DOCUMENTS
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default ClientPortal
