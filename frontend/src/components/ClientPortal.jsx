import { useState, useRef, useEffect } from 'react'
import './ClientPortal.css'
import Logo from './Logo'
import INEScanner from './INEScanner'
import CardSwap, { Card } from './CardSwap'
import CreditCard from './CreditCard'
import { API_URL } from '../config'

// ── Helpers ────────────────────────────────────────────────────────────────
const STEPS = ['upload', 'rfc', 'income', 'credit']
const KYC_PRECHECK_STEPS = [
  'Permite el acceso a la cámara cuando tu navegador lo solicite.',
  'Captura claramente el frente de tu identificación oficial.',
  'Captura claramente la parte trasera de tu identificación oficial.',
  'Completa la prueba biométrica facial mirando directamente a la cámara.',
]

const incomeRangeToNumber = (range) => ({
  '5-15':  10000,
  '15-30': 22500,
  '30-50': 40000,
  '50+':   60000,
}[range] ?? 0)

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
  const [step,          setStep]          = useState('landing')
  const [authEmail,     setAuthEmail]     = useState('')
  const [authPassword,  setAuthPassword]  = useState('')
  const [authConfirm,   setAuthConfirm]   = useState('')
  const [authError,     setAuthError]     = useState(null)
  const [uploadedFile,  setUploadedFile]  = useState(null)
  const [isDragging,    setIsDragging]    = useState(false)
  const [rfc,           setRfc]           = useState('')
  const [email,         setEmail]         = useState('')
  const [incomeType,    setIncomeType]    = useState(null)
  const [incomeRange,   setIncomeRange]   = useState(null)
  const [creditLine,    setCreditLine]    = useState(0)
  const [capturedName,  setCapturedName]  = useState('')
  const [capturedINEFile, setCapturedINEFile] = useState(null)
  const [applicationId, setApplicationId] = useState(null)
  const [submitError,   setSubmitError]   = useState(null)
  const fileInputRef = useRef(null)

  // KYC capture — store name + INE image blob
  const handleCapture = (image, mode, name) => {
    if (mode === 'face') {
      if (name) setCapturedName(name)
      if (image) setCapturedINEFile(image)
      setStep('complete')
    }
  }

  const handleActivar = async () => {
    setSubmitError(null)
    setStep('loading')
    try {
      // 1. Create the loan application
      const res = await fetch(`${API_URL}/api/loans`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          applicantName:  capturedName || rfc,
          applicantEmail: email,
          loanAmount:     creditLine,
          applicationType: 'CREDIT_CARD',
          monthlyIncome:  incomeRangeToNumber(incomeRange),
          existingDebt:   0,
        }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()

      // 2. Upload INE scan to S3 if URL provided
      if (capturedINEFile && data.uploadUrls?.ine) {
        await fetch(data.uploadUrls.ine.url, {
          method: 'PUT',
          body: capturedINEFile,
          headers: { 'Content-Type': 'application/pdf' },
        })
      }

      // 3. Upload proof of address to S3 if URL provided
      if (uploadedFile && data.uploadUrls?.proof_of_address) {
        await fetch(data.uploadUrls.proof_of_address.url, {
          method: 'PUT',
          body: uploadedFile,
          headers: { 'Content-Type': uploadedFile.type },
        })
      }

      setApplicationId(data.applicationId)
      setStep('confirmed')
    } catch (err) {
      console.error(err)
      setSubmitError('Algo salió mal. Intenta de nuevo.')
      setStep('credit')
    }
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

  const handleAuthLogin = (e) => {
    e.preventDefault()
    setAuthError(null)

    const email = authEmail.trim()
    if (!email || !authPassword) {
      setAuthError('Ingresa correo y contraseña para continuar.')
      return
    }

    setEmail(email)
    setStep('kyc-intro')
  }

  const handleAuthRegister = (e) => {
    e.preventDefault()
    setAuthError(null)

    const email = authEmail.trim()
    if (!email || !authPassword || !authConfirm) {
      setAuthError('Completa todos los campos para crear tu cuenta.')
      return
    }

    if (authPassword !== authConfirm) {
      setAuthError('Las contraseñas no coinciden.')
      return
    }

    setEmail(email)
    setStep('kyc-intro')
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
            <button className="liquid-btn kyc-cta" onClick={() => setStep('auth-choice')}>
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

      {/* ── AUTH CHOICE ── */}
      {step === 'auth-choice' && (
        <div className="kyc-card glass-panel kyc-auth-card">
          <span className="auth-choice-badge">Acceso seguro</span>
          <div className="kyc-intro">
            <h1>Acceso al portal</h1>
            <p>Selecciona cómo deseas continuar.</p>
          </div>

          <div className="auth-choice-actions">
            <button
              type="button"
              className="auth-mode-btn"
              onClick={() => { setAuthError(null); setAuthConfirm(''); setStep('auth-login') }}
            >
              <span className="auth-mode-icon" aria-hidden="true">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
              </span>
              <span className="auth-mode-copy">
                <strong>Ya soy cliente</strong>
                <small>Ingresar con correo y contraseña.</small>
              </span>
            </button>
            <button
              type="button"
              className="auth-mode-btn"
              onClick={() => { setAuthError(null); setStep('auth-register') }}
            >
              <span className="auth-mode-icon" aria-hidden="true">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 5v14" />
                  <path d="M5 12h14" />
                  <circle cx="12" cy="12" r="9" />
                </svg>
              </span>
              <span className="auth-mode-copy">
                <strong>Soy cliente nuevo</strong>
                <small>Crear cuenta para acceder al portal.</small>
              </span>
            </button>
          </div>

          <p className="auth-trust-note">
            <span aria-hidden="true">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="10" rx="2" />
                <path d="M7 11V8a5 5 0 0 1 10 0v3" />
              </svg>
            </span>
            Sesión cifrada SSL/TLS
          </p>

          <div className="kyc-intro-actions">
            <button type="button" className="liquid-btn kyc-ghost-btn" onClick={() => setStep('landing')}>
              Volver
            </button>
          </div>
        </div>
      )}

      {/* ── AUTH LOGIN ── */}
      {step === 'auth-login' && (
        <div className="kyc-card glass-panel kyc-auth-card">
          <div className="kyc-intro">
            <h1>Iniciar sesión</h1>
            <p>Ingresa con tu cuenta existente.</p>
          </div>

          <form className="auth-form" onSubmit={handleAuthLogin}>
            <label className="auth-field">
              <span>Correo electrónico</span>
              <input
                type="email"
                value={authEmail}
                onChange={(e) => setAuthEmail(e.target.value)}
                placeholder="tu@correo.com"
                autoComplete="email"
              />
            </label>

            <label className="auth-field">
              <span>Contraseña</span>
              <input
                type="password"
                value={authPassword}
                onChange={(e) => setAuthPassword(e.target.value)}
                placeholder="Ingresa tu contraseña"
                autoComplete="current-password"
              />
            </label>

            {authError && <p className="auth-error">{authError}</p>}

            <div className="kyc-intro-actions">
              <button type="button" className="liquid-btn kyc-ghost-btn" onClick={() => setStep('auth-choice')}>
                Volver
              </button>
              <button type="submit" className="liquid-btn">
                Ingresar
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ── AUTH REGISTER ── */}
      {step === 'auth-register' && (
        <div className="kyc-card glass-panel kyc-auth-card">
          <div className="kyc-intro">
            <h1>Crear cuenta</h1>
            <p>Regístrate con correo y contraseña para el portal.</p>
          </div>

          <form className="auth-form" onSubmit={handleAuthRegister}>
            <label className="auth-field">
              <span>Correo electrónico</span>
              <input
                type="email"
                value={authEmail}
                onChange={(e) => setAuthEmail(e.target.value)}
                placeholder="tu@correo.com"
                autoComplete="email"
              />
            </label>

            <label className="auth-field">
              <span>Contraseña</span>
              <input
                type="password"
                value={authPassword}
                onChange={(e) => setAuthPassword(e.target.value)}
                placeholder="Crea una contraseña"
                autoComplete="new-password"
              />
            </label>

            <label className="auth-field">
              <span>Confirmar contraseña</span>
              <input
                type="password"
                value={authConfirm}
                onChange={(e) => setAuthConfirm(e.target.value)}
                placeholder="Confirma tu contraseña"
                autoComplete="new-password"
              />
            </label>

            {authError && <p className="auth-error">{authError}</p>}

            <div className="kyc-intro-actions">
              <button type="button" className="liquid-btn kyc-ghost-btn" onClick={() => setStep('auth-choice')}>
                Volver
              </button>
              <button type="submit" className="liquid-btn">
                Crear cuenta
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ── KYC INTRO ── */}
      {step === 'kyc-intro' && (
        <div className="kyc-card glass-panel kyc-intro-card">
          <span className="kyc-intro-badge">Preparación de verificación</span>
          <div className="kyc-id-logo" aria-hidden="true">
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="5" width="18" height="14" rx="2" />
              <circle cx="9" cy="12" r="2.2" />
              <path d="M13.5 10h4" />
              <path d="M13.5 13h4" />
              <path d="M7 16h10" />
            </svg>
          </div>
          <div className="kyc-intro">
            <h1>Vamos a verificar tu identidad.</h1>
            <p>Completa los siguientes pasos en orden:</p>
          </div>

          <div className="kyc-steps-list">
            {KYC_PRECHECK_STEPS.map((stepText, idx) => (
              <div key={stepText} className="kyc-step-item">
                <span className="kyc-step-index">{idx + 1}</span>
                <p>{stepText}</p>
              </div>
            ))}
          </div>

          <div className="privacy-notice">
            <div className="privacy-notice-icon" aria-hidden="true">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <path d="M9 12l2 2 4-4" />
              </svg>
            </div>
            <p>
              <strong>Aviso de privacidad:</strong> Tus datos de identificación y biométricos se cifran y se utilizan únicamente para verificar tu identidad, prevenir fraudes y cumplir con requisitos legales.
            </p>
          </div>

          <div className="kyc-intro-actions">
            <button className="liquid-btn kyc-ghost-btn" onClick={() => setStep('auth-choice')}>
              Volver
            </button>
            <button className="liquid-btn" onClick={() => setStep('kyc')}>
              Continuar
            </button>
          </div>
        </div>
      )}

      {/* ── KYC CAMERA ── */}
      {step === 'kyc' && (
        <div className="portal-card glass-panel scanner-mode">
          <div className="scanner-view">
            <INEScanner onCapture={handleCapture} onBack={() => setStep('kyc-intro')} />
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

          <div className="rfc-field" style={{ marginTop: '12px' }}>
            <input
              className="rfc-input"
              type="email"
              placeholder="correo@ejemplo.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <button className="liquid-btn kyc-cta"
            disabled={rfc.length < 12 || !email.includes('@')}
            style={{ opacity: (rfc.length >= 12 && email.includes('@')) ? 1 : 0.35, cursor: (rfc.length >= 12 && email.includes('@')) ? 'pointer' : 'not-allowed' }}
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

          {submitError && (
            <p style={{ color: 'var(--error, #f87171)', fontSize: '13px', textAlign: 'center', marginTop: '8px' }}>
              {submitError}
            </p>
          )}

          <button className="liquid-btn kyc-cta" onClick={handleActivar}>
            Activar mi tarjeta →
          </button>
        </div>
      )}

      {/* ── LOADING ── */}
      {step === 'loading' && (
        <div className="kyc-card glass-panel kyc-complete-card">
          <div className="check-ring" style={{ opacity: 0.6 }}>
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
              <circle cx="32" cy="32" r="30" stroke="#60a5fa" strokeWidth="1.5" opacity="0.3"/>
              <path d="M32 8 A24 24 0 0 1 56 32"
                stroke="#60a5fa" strokeWidth="2.5"
                strokeLinecap="round"
                style={{ animation: 'spin 1s linear infinite', transformOrigin: '32px 32px' }}
              />
            </svg>
          </div>
          <p className="complete-label">Enviando solicitud…</p>
        </div>
      )}

      {/* ── CONFIRMED ── */}
      {step === 'confirmed' && (
        <div className="kyc-card glass-panel kyc-complete-card">
          <div className="check-ring">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
              <circle cx="32" cy="32" r="30" stroke="#6ee7b7" strokeWidth="1.5" opacity="0.2"/>
              <path className="check-path" d="M18 32 L27 41 L46 22"
                stroke="#6ee7b7" strokeWidth="2.5"
                strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <p className="complete-label">¡Solicitud enviada!</p>
          <p className="detail-id" style={{ fontFamily: 'monospace', fontSize: '18px', color: 'var(--text-primary)', marginTop: '8px' }}>
            Folio: {applicationId?.slice(0, 8).toUpperCase()}
          </p>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '8px', textAlign: 'center' }}>
            Te notificaremos a <strong>{email}</strong> en máximo 2 horas.
          </p>
        </div>
      )}

    </div>
  )
}

export default ClientPortal
