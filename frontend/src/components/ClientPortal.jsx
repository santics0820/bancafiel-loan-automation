import { useState, useRef, useEffect } from 'react'
import './ClientPortal.css'
import Logo from './Logo'
import INEScanner from './INEScanner'
import CardSwap, { Card } from './CardSwap'
import CreditCard from './CreditCard'

// ── Helpers ────────────────────────────────────────────────────────────────
const STEPS = ['upload', 'rfc', 'income', 'credit']

function StepDots({ step }) {
  const idx = STEPS.indexOf(step)
  return (
    <div className="step-dots">
      {STEPS.map((s, i) => (
        <div key={s} className={`step-dot ${i < idx ? 'done' : i === idx ? 'active' : ''}`} />
      ))}
    </div>
  )
}

const INCOME_TYPES = [
  {
    key: 'asalariado', label: 'Asalariado',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="7" width="20" height="14" rx="2"/>
        <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
      </svg>
    ),
  },
  {
    key: 'independiente', label: 'Independiente',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="13" rx="2"/>
        <path d="M8 21h8"/><path d="M12 17v4"/>
      </svg>
    ),
  },
  {
    key: 'empresario', label: 'Empresario',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 22h20"/>
        <path d="M6 2h12a2 2 0 0 1 2 2v18H4V4a2 2 0 0 1 2-2z"/>
        <path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/>
      </svg>
    ),
  },
  {
    key: 'pensionado', label: 'Pensionado',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        <path d="M9 12l2 2 4-4"/>
      </svg>
    ),
  },
]

const INCOME_RANGES = [
  { key: '5-15',  label: '$5k – $15k' },
  { key: '15-30', label: '$15k – $30k' },
  { key: '30-50', label: '$30k – $50k' },
  { key: '50+',   label: '$50k+' },
]

function computeCredit(type, range) {
  const mult = { asalariado: 1, independiente: 0.9, empresario: 1.3, pensionado: 0.75 }
  const base = { '5-15': 12000, '15-30': 30000, '30-50': 55000, '50+': 90000 }
  return Math.min(Math.round((base[range] * mult[type]) / 1000) * 1000, 100000)
}

function getCardTier(amount) {
  if (amount >= 60000) return { label: 'BANCAFIEL ORO',     cls: 'tier-gold'    }
  if (amount >= 20000) return { label: 'BANCAFIEL CLÁSICA', cls: 'tier-classic' }
  return                      { label: 'BANCAFIEL BÁSICA',  cls: 'tier-basic'   }
}

// ── Component ──────────────────────────────────────────────────────────────
function ClientPortal({ active }) {
  const [step,        setStep]        = useState('landing')
  const [uploadedFile, setUploadedFile] = useState(null)
  const [isDragging,   setIsDragging]   = useState(false)
  const [rfc,          setRfc]          = useState('')
  const [incomeType,   setIncomeType]   = useState(null)
  const [incomeRange,  setIncomeRange]  = useState(null)
  const [creditLine,   setCreditLine]   = useState(0)
  const fileInputRef = useRef(null)

  // KYC capture (INEScanner only calls this)
  const handleCapture = (image, mode) => {
    if (mode === 'face') setStep('complete')
  }

  // Auto-advance: KYC complete → upload
  useEffect(() => {
    if (step !== 'complete') return
    const t = setTimeout(() => setStep('upload'), 1800)
    return () => clearTimeout(t)
  }, [step])

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) setUploadedFile(file)
  }

  const goToCredit = () => {
    setCreditLine(computeCredit(incomeType, incomeRange))
    setStep('credit')
  }

  if (!active) return null

  const tier = getCardTier(creditLine)

  return (
    <div className="client-view">

      {/* ── LANDING ── */}
      {step === 'landing' && (
        <div className="kyc-landing-split glass-panel">

          {/* Left: copy + CTA */}
          <div className="kyc-landing-left">
            <Logo />
            <div className="kyc-intro">
              <h1>Solicita tu tarjeta</h1>
              <p>100% digital · Menos de 5 minutos</p>
            </div>
            <button className="liquid-btn kyc-cta" onClick={() => setStep('kyc')}>
              Empezar
            </button>
          </div>

          {/* Right: animated card stack */}
          <div className="kyc-landing-right">
            <CardSwap
              width={300}
              height={190}
              cardDistance={44}
              verticalDistance={30}
              delay={3200}
              pauseOnHover={false}
              skewAmount={4}
              easing="elastic"
            >
              <Card>
                <CreditCard type="gray-dark" tier="BÁSICA"   number="•••• •••• •••• 1204" expiry="09/27" />
              </Card>
              <Card>
                <CreditCard type="blue-dark" tier="CLÁSICA"  number="•••• •••• •••• 5589" expiry="03/28" />
              </Card>
              <Card>
                <CreditCard type="gold-dark" tier="ORO"      number="•••• •••• •••• 8831" expiry="11/29" />
              </Card>
            </CardSwap>
          </div>

        </div>
      )}

      {/* ── KYC CAMERA ── */}
      {step === 'kyc' && (
        <div className="portal-card glass-panel scanner-mode">
          <div className="scanner-view">
            <INEScanner onCapture={handleCapture} onBack={() => setStep('landing')} />
          </div>
        </div>
      )}

      {/* ── KYC COMPLETE (auto-advances) ── */}
      {step === 'complete' && (
        <div className="kyc-card glass-panel kyc-complete-card">
          <div className="check-ring">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
              <circle cx="32" cy="32" r="30" stroke="#6ee7b7" strokeWidth="1.5" opacity="0.2"/>
              <path className="check-path" d="M18 32 L27 41 L46 22"
                stroke="#6ee7b7" strokeWidth="2.5"
                strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <p className="complete-label">Identidad verificada</p>
        </div>
      )}

      {/* ── COMPROBANTE ── */}
      {step === 'upload' && (
        <div className="kyc-card glass-panel">
          <StepDots step="upload" />

          <div className="kyc-intro">
            <h1>Comprobante de domicilio</h1>
            <p>Recibo de luz, agua o estado de cuenta.<br/>No mayor a 3 meses.</p>
          </div>

          <div
            className={`upload-drop-zone ${isDragging ? 'dragging' : ''} ${uploadedFile ? 'has-file' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            {uploadedFile ? (
              <div className="upload-file-preview">
                <div className="upload-file-icon">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                  </svg>
                </div>
                <div className="upload-file-info">
                  <span className="upload-file-name">{uploadedFile.name}</span>
                  <span className="upload-file-size">{(uploadedFile.size / 1024 / 1024).toFixed(2)} MB</span>
                </div>
                <button className="upload-remove"
                  onClick={(e) => { e.stopPropagation(); setUploadedFile(null) }}>✕</button>
              </div>
            ) : (
              <div className="upload-empty">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                <span>PDF · JPG · PNG · max 10 MB</span>
              </div>
            )}
          </div>

          <input ref={fileInputRef} type="file" accept=".pdf,.jpg,.jpeg,.png"
            style={{ display: 'none' }}
            onChange={(e) => { const f = e.target.files[0]; if (f) setUploadedFile(f) }}
          />

          <button className="liquid-btn kyc-cta"
            disabled={!uploadedFile}
            style={{ opacity: uploadedFile ? 1 : 0.35, cursor: uploadedFile ? 'pointer' : 'not-allowed' }}
            onClick={() => setStep('rfc')}
          >
            Continuar →
          </button>
        </div>
      )}

      {/* ── RFC ── */}
      {step === 'rfc' && (
        <div className="kyc-card glass-panel">
          <StepDots step="rfc" />

          <div className="kyc-intro">
            <h1>¿Cuál es tu RFC?</h1>
            <p>Lo encontrarás en tu constancia fiscal del SAT.</p>
          </div>

          <div className="rfc-field">
            <input
              className="rfc-input"
              type="text"
              placeholder="CURP000000XX0"
              maxLength={13}
              value={rfc}
              onChange={(e) => setRfc(e.target.value.toUpperCase().replace(/[^A-Z0-9Ñ]/g, ''))}
              autoFocus
            />
            <span className="rfc-hint">{rfc.length} / 12–13 caracteres</span>
          </div>

          <button className="liquid-btn kyc-cta"
            disabled={rfc.length < 12}
            style={{ opacity: rfc.length >= 12 ? 1 : 0.35, cursor: rfc.length >= 12 ? 'pointer' : 'not-allowed' }}
            onClick={() => setStep('income')}
          >
            Continuar →
          </button>
        </div>
      )}

      {/* ── INGRESOS ── */}
      {step === 'income' && (
        <div className="kyc-card glass-panel">
          <StepDots step="income" />

          <div className="kyc-intro">
            <h1>¿Cómo obtienes tus ingresos?</h1>
            <p>Selecciona tu situación y rango mensual.</p>
          </div>

          <div className="income-types">
            {INCOME_TYPES.map(t => (
              <button
                key={t.key}
                className={`income-type-card ${incomeType === t.key ? 'selected' : ''}`}
                onClick={() => setIncomeType(t.key)}
              >
                {t.icon}
                <span>{t.label}</span>
              </button>
            ))}
          </div>

          <div className={`income-ranges ${incomeType ? 'visible' : ''}`}>
            {INCOME_RANGES.map(r => (
              <button
                key={r.key}
                className={`income-range-chip ${incomeRange === r.key ? 'selected' : ''}`}
                onClick={() => setIncomeRange(r.key)}
              >
                {r.label}
              </button>
            ))}
          </div>

          <button className="liquid-btn kyc-cta"
            disabled={!incomeType || !incomeRange}
            style={{ opacity: (incomeType && incomeRange) ? 1 : 0.35, cursor: (incomeType && incomeRange) ? 'pointer' : 'not-allowed' }}
            onClick={goToCredit}
          >
            Ver mi línea →
          </button>
        </div>
      )}

      {/* ── LÍNEA DE CRÉDITO ── */}
      {step === 'credit' && (
        <div className="kyc-card glass-panel">
          <StepDots step="credit" />

          <div className="kyc-intro">
            <p>Línea de crédito aprobada</p>
          </div>

          <div className="credit-display">
            <span className="credit-amount">
              ${creditLine.toLocaleString('es-MX')}
            </span>
            <span className={`credit-tier ${tier.cls}`}>{tier.label}</span>
          </div>

          <div className="credit-details">
            <div className="credit-detail-row">
              <span>RFC registrado</span>
              <span className="detail-val">{rfc}</span>
            </div>
            <div className="credit-detail-row">
              <span>Tipo de ingreso</span>
              <span className="detail-val" style={{ textTransform: 'capitalize' }}>{incomeType}</span>
            </div>
            <div className="credit-detail-row">
              <span>Rango mensual</span>
              <span className="detail-val">{INCOME_RANGES.find(r => r.key === incomeRange)?.label}</span>
            </div>
          </div>

          <button className="liquid-btn kyc-cta">
            Activar mi tarjeta →
          </button>
        </div>
      )}

    </div>
  )
}

export default ClientPortal
