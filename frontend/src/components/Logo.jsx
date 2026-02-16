import './Logo.css'

function Logo({ className = '' }) {
  return (
    <div className={`logo ${className}`}>
      <div className="logo-mark"></div>
      BANCAFIEL
    </div>
  )
}

export default Logo
