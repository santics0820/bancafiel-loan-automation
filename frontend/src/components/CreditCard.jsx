import './CreditCard.css'

const PaypassIcon = ({ className = '' }) => (
  <svg className={className} width="18" height="22" viewBox="0 0 18 22" fill="none"
    stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
    <circle cx="9" cy="19.5" r="1.5" fill="currentColor" stroke="none"/>
    <path d="M5.5 15.5 a4.5 4.5 0 0 1 7 0"/>
    <path d="M2 11.5 a8.5 8.5 0 0 1 14 0"/>
  </svg>
)

const MastercardIcon = () => (
  <svg width="34" height="22" viewBox="0 0 34 22" fill="none">
    <circle cx="13" cy="11" r="8" fill="#EB001B"/>
    <circle cx="21" cy="11" r="8" fill="#F79E1B" fillOpacity="0.92"/>
  </svg>
)

const MastercardIconWhite = () => (
  <svg width="34" height="22" viewBox="0 0 34 22" fill="none">
    <circle cx="13" cy="11" r="8" fill="white" fillOpacity="0.75"/>
    <circle cx="21" cy="11" r="8" fill="white" fillOpacity="0.45"/>
  </svg>
)

const darkTypes = ['gray-dark', 'blue-dark', 'gold-dark']

function CreditCard({
  type     = 'gray-dark',
  tier     = 'CLÁSICA',
  number   = '•••• •••• •••• 4821',
  expiry   = '12/28',
  holder   = 'J. PÉREZ MENDOZA',
}) {
  const useDark = darkTypes.includes(type)

  return (
    <div className={`cc-card cc-${type}`}>
      <div className="cc-shine" />

      {/* Top: brand + paypass */}
      <div className="cc-top">
        <span className="cc-brand">BANCAFIEL</span>
        <PaypassIcon className="cc-paypass" />
      </div>

      {/* Chip */}
      <svg className="cc-chip" width="36" height="28" viewBox="0 0 36 28" fill="none">
        <rect x="0.5" y="0.5" width="35" height="27" rx="4"
          fill="rgba(210,175,60,0.88)" stroke="rgba(170,130,20,0.4)" strokeWidth="0.5"/>
        <line x1="0"    y1="9.5"  x2="36" y2="9.5"  stroke="rgba(130,90,10,0.45)" strokeWidth="0.5"/>
        <line x1="0"    y1="18.5" x2="36" y2="18.5" stroke="rgba(130,90,10,0.45)" strokeWidth="0.5"/>
        <line x1="11.5" y1="0"    x2="11.5" y2="28" stroke="rgba(130,90,10,0.45)" strokeWidth="0.5"/>
        <line x1="24.5" y1="0"    x2="24.5" y2="28" stroke="rgba(130,90,10,0.45)" strokeWidth="0.5"/>
        <rect x="11.5" y="9.5" width="13" height="9" fill="rgba(170,130,20,0.25)"/>
      </svg>

      {/* Bottom: holder + expiry + mastercard */}
      <div className="cc-bottom">
        <div className="cc-bottom-left">
          <div className="cc-field">
            <span className="cc-label">TITULAR</span>
            <span className="cc-value">{holder}</span>
          </div>
          <div className="cc-number-row">
            <span className="cc-number">{number}</span>
            <span className="cc-expiry">{expiry}</span>
          </div>
        </div>

        <div className="cc-mc-wrap">
          {useDark ? <MastercardIcon /> : <MastercardIconWhite />}
        </div>
      </div>

      <span className="cc-tier">{tier}</span>
    </div>
  )
}

export default CreditCard
