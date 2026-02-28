# Frontend API Wiring — Fernando's Task List

**Owner:** Fernando (`nitrofgm`)
**Branch:** `feature/fernando-api-wiring` (branch off `dev`)
**API Base URL:** `https://nfgxyb0os2.execute-api.us-east-1.amazonaws.com/dev`

---

## Step 0 — Create `frontend/src/config.js` (5 min)

Create this file first. Every component imports from here.

```js
export const API_URL = 'https://nfgxyb0os2.execute-api.us-east-1.amazonaws.com/dev'
```

---

## Step 1 — `ClientPortal.jsx`

### 1a. Add email input field (NEW UI element required)
The backend requires `applicantEmail` to create an application. Fernando needs to add an
email input step in the flow — best placed in the `rfc` step or as a new step between
`rfc` and `income`.

```jsx
// Add to state
const [email, setEmail] = useState('')

// Add input field in the rfc step (or its own step):
<input
  className="rfc-input"
  type="email"
  placeholder="correo@ejemplo.com"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
/>
```

### 1b. Wire "Activar mi tarjeta →" button → `POST /api/loans`

**Currently:** button does nothing
**Required:** call the API to create the application, then upload documents to S3

```js
import { API_URL } from '../config'

// Replace the onClick of "Activar mi tarjeta →" button:
const handleActivar = async () => {
  setStep('loading') // add a loading state

  // 1. Create the application
  const res = await fetch(`${API_URL}/api/loans`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      applicantName: capturedName,       // from INEScanner capture
      applicantEmail: email,             // from new email field
      loanAmount: creditLine,            // already computed
      applicationType: 'CREDIT_CARD',
      monthlyIncome: incomeRangeToNumber(incomeRange), // map range to number
      existingDebt: 0
    })
  })
  const data = await res.json()
  // data = { applicationId, status, uploadUrls: { ine, proof_of_address, bank_statement } }

  // 2. Upload INE scan to S3 (direct PUT, no auth needed)
  if (capturedINEFile && data.uploadUrls?.ine) {
    await fetch(data.uploadUrls.ine.url, {
      method: 'PUT',
      body: capturedINEFile,
      headers: { 'Content-Type': 'application/pdf' }
    })
  }

  // 3. Upload proof of address to S3
  if (uploadedFile && data.uploadUrls?.proof_of_address) {
    await fetch(data.uploadUrls.proof_of_address.url, {
      method: 'PUT',
      body: uploadedFile,
      headers: { 'Content-Type': uploadedFile.type }
    })
  }

  // 4. Show confirmation with applicationId
  setApplicationId(data.applicationId)
  setStep('confirmed')
}
```

### 1c. Add confirmation step (NEW UI element required)
After a successful submit, show the application ID to the customer.

```jsx
{step === 'confirmed' && (
  <div className="kyc-card glass-panel">
    <div className="check-ring">...</div>
    <p className="complete-label">¡Solicitud enviada!</p>
    <p className="detail-id">Folio: {applicationId?.slice(0,8).toUpperCase()}</p>
    <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
      Te notificaremos a {email} en máximo 2 horas.
    </p>
  </div>
)}
```

### 1d. Helper: map incomeRange key → number
```js
const incomeRangeToNumber = (range) => ({
  '5-15':  10000,
  '15-30': 22500,
  '30-50': 40000,
  '50+':   60000
}[range] ?? 0)
```

---

## Step 2 — `AnalystDashboard.jsx`

### 2a. Replace hardcoded `const applications = [...]` → fetch from API

**Currently:** 4 hardcoded objects at the top of the file
**Required:** load real applications on mount

```js
import { useState, useEffect } from 'react'
import { API_URL } from '../config'

function AnalystDashboard({ active }) {
  const [applications, setApplications]   = useState([])
  const [selectedApp,  setSelectedApp]    = useState(null)
  const [loading,      setLoading]        = useState(true)
  const [currentView,  setCurrentView]    = useState('applications')

  useEffect(() => {
    if (!active) return
    fetch(`${API_URL}/api/loans?status=pending`)
      .then(r => r.json())
      .then(data => {
        setApplications(data.applications ?? [])
        setSelectedApp(data.applications?.[0] ?? null)
        setLoading(false)
      })
  }, [active])
  ...
}
```

### 2b. Map API fields to what the UI already uses

The backend returns these fields — map them to what the existing UI renders:

| UI field | API field | Notes |
|---|---|---|
| `app.id` | `app.id` | UUID — show first 8 chars: `app.id.slice(0,8).toUpperCase()` |
| `app.name` | `app.applicantName` | rename |
| `app.risk` | `app.fraudRiskLevel` | `'low'/'medium'/'high'` → already matches riskColors |
| `app.creditScore` | `app.creditScore` | direct |
| `app.details.requestedAmount` | `app.loanAmount` | format: `$${app.loanAmount.toLocaleString('es-MX')} MXN` |
| `app.details.fraudProbability` | `app.fraudScore` | format: `${(app.fraudScore*100).toFixed(1)}%` |
| `app.details.incomeVerification` | from `app.extractedData` | call `GET /api/loans/{id}` on click |
| `app.details.employer` | from `app.extractedData.employer_name` | call `GET /api/loans/{id}` on click |
| `app.details.aiAnalysis` | `app.creditRecommendation` | use as text |
| `app.time` | `app.requestedDate` | format with `timeAgo(app.requestedDate)` |

### 2c. Load full detail on app click → `GET /api/loans/{id}`

```js
const handleSelectApp = async (app) => {
  setSelectedApp(app) // show basic info immediately
  const res = await fetch(`${API_URL}/api/loans/${app.id}`)
  const detail = await res.json()
  setSelectedApp({
    ...app,
    details: {
      requestedAmount: `$${detail.loanAmount?.toLocaleString('es-MX')} MXN`,
      fraudProbability: `${((detail.fraudScore ?? 0) * 100).toFixed(1)}% (${detail.fraudRiskLevel ?? '-'})`,
      incomeVerification: detail.extractedData?.net_income ? 'VERIFICADO' : 'PENDIENTE',
      employer: detail.extractedData?.employer_name ?? '-',
      employment: detail.extractedData?.payment_frequency ?? '-',
      aiAnalysis: detail.creditRecommendation ?? 'Pendiente de análisis',
      identityMatch: detail.extractedData?.curp ? '99.8% VERIFICADO' : 'PENDIENTE',
      monthlyRent: detail.existingDebt ? `$${detail.existingDebt?.toLocaleString('es-MX')} MXN` : '-',
      term: '-',
    },
    history: detail.history ?? []
  })
}
```

### 2d. Wire "APROBAR" button → `POST /api/loans/{id}/approve`

```js
const handleApprove = async () => {
  const res = await fetch(`${API_URL}/api/loans/${selectedApp.id}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approvedBy: 'analyst', notes: 'Aprobado desde dashboard' })
  })
  if (res.ok) {
    // Remove from list and show next application
    setApplications(prev => prev.filter(a => a.id !== selectedApp.id))
    setSelectedApp(applications.find(a => a.id !== selectedApp.id) ?? null)
  }
}

// In JSX:
<button className="action-btn liquid-btn" onClick={handleApprove}>APROBAR</button>
```

### 2e. Wire "RECHAZAR" button → `POST /api/loans/{id}/reject`

```js
const handleReject = async () => {
  const res = await fetch(`${API_URL}/api/loans/${selectedApp.id}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rejectedBy: 'analyst', reason: 'Rechazado desde dashboard' })
  })
  if (res.ok) {
    setApplications(prev => prev.filter(a => a.id !== selectedApp.id))
    setSelectedApp(applications.find(a => a.id !== selectedApp.id) ?? null)
  }
}

// In JSX:
<button className="action-btn reject" onClick={handleReject}>RECHAZAR</button>
```

### 2f. Update hardcoded count "SOLICITUDES (4)" in nav

```jsx
// Replace hardcoded 4:
<button ...>SOLICITUDES ({applications.length})</button>
```

---

## Step 3 — `Overview.jsx`

### 3a. Replace hardcoded `const statsData` → `GET /api/analytics`

**Currently:** all numbers are fake
**Required:** fetch real analytics on mount

```js
import { useEffect, useState } from 'react'
import { API_URL } from '../config'

function Overview({ active }) {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    if (!active) return
    const today = new Date().toISOString().split('T')[0]
    const start = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    fetch(`${API_URL}/api/analytics?startDate=${start}&endDate=${today}`)
      .then(r => r.json())
      .then(setStats)
  }, [active])

  if (!stats) return <div>Cargando...</div>
  ...
}
```

### 3b. Map API fields to what the UI shows

| UI field | API field |
|---|---|
| `totalApplications` | `stats.totalApplications` |
| `pendingReview` | `stats.pending` |
| `approved` | `stats.approved` |
| `rejected` | `stats.rejected` |
| `successRate` | `(stats.approvalRate * 100).toFixed(1) + '%'` |
| `avgProcessingTime` | `stats.averageProcessingTime.toFixed(1) + ' MIN'` |
| `fraudAlerts` (new) | `stats.fraudAlerts` |
| chart data | `stats.volumeByDay` — array of `{ date, applications }` |

### 3c. Replace hardcoded `recentActivity` → `GET /api/loans`

```js
// Fetch last 6 applications across all statuses for the activity feed:
fetch(`${API_URL}/api/loans?status=pending`)
  .then(r => r.json())
  .then(data => setRecentActivity(data.applications.slice(0, 6)))
```

---

## Step 4 — `LiquidDashboard.jsx`

**Skip** — this is a personal banking UI showcase (balance, transactions, transfers).
It is not part of the loan pipeline. Leave all data hardcoded for the demo.

---

## What NOT to touch

- All CSS files — design is done, do not change
- `INEScanner.jsx` — camera logic works, just pass captured image to Step 1b
- `CardSwap.jsx`, `CreditCard.jsx`, `Logo.jsx`, `ViewToggle.jsx` — purely visual, no wiring needed

---

## Error handling pattern (use everywhere)

```js
try {
  const res = await fetch(...)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const data = await res.json()
  // handle success
} catch (err) {
  console.error(err)
  // show user-friendly error message in UI
  setError('Algo salió mal. Intenta de nuevo.')
}
```

---

## Git workflow reminder

```bash
git checkout dev
git pull origin dev
git checkout -b feature/fernando-api-wiring
# ... make changes ...
git add frontend/src/...
git commit -m "feat: wire frontend to backend API"
git push origin feature/fernando-api-wiring
# Open PR to dev on GitHub — Santiago reviews before merging
```
