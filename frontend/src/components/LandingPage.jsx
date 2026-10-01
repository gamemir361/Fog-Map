export function LandingPage({ onOpenLogin, onOpenRegister }) {
  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        background: 'radial-gradient(circle at 50% 30%, #1e293b 0%, #0f172a 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 2500,
        padding: '20px',
        color: '#f8fafc',
        fontFamily: 'Vazirmatn, sans-serif',
      }}>
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '460px',
          padding: '40px 32px',
          borderRadius: '24px',
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '24px',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.6)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
        }}>
        {/* App Logo */}
        <div
          style={{
            width: '80px',
            height: '80px',
            borderRadius: '24px',
            background: 'linear-gradient(135deg, #38bdf8, #8b5cf6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '40px',
            boxShadow: '0 10px 30px rgba(56, 189, 248, 0.4)',
          }}>
          🌫️
        </div>

        {/* Header Title & Tagline */}
        <div>
          <h1
            style={{
            fontSize: '24px',
            fontWeight: 900,
            background: 'linear-gradient(135deg, #38bdf8, #a855f7)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            margin: '0 0 8px 0',
          }}>
            نقشه مه‌جنگ و هیت‌مپ تهران
          </h1>
          <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0, lineHeight: 1.6 }}>
            سامانه کاوش کلان‌شهر تهران. در دنیای واقعی قدم بزنید، مه ناشناخته‌های شهر را کنار بزنید و هیت‌مپ مسیرهای خود را کشف کنید.
          </p>
        </div>

        {/* Feature Highlights */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '10px',
            width: '100%',
            textAlign: 'right',
            fontSize: '11px',
            color: '#cbd5e1',
          }}>
          <div style={{ background: 'rgba(255,255,255,0.05)', padding: '10px 12px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '16px' }}>🌫️</span>
            <span>مه‌جنگ بلورین روی نقشه</span>
          </div>
          <div style={{ background: 'rgba(255,255,255,0.05)', padding: '10px 12px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '16px' }}>🌡️</span>
            <span>هیت‌مپ حرارتی نقاط کشف‌شده</span>
          </div>
          <div style={{ background: 'rgba(255,255,255,0.05)', padding: '10px 12px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '16px' }}>🛰️</span>
            <span>ردیابی زنده با GPS و کلیک</span>
          </div>
          <div style={{ background: 'rgba(255,255,255,0.05)', padding: '10px 12px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '16px' }}>📊</span>
            <span>محاسبه مساحت با PostGIS</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%', marginTop: '8px' }}>
          <button
            onClick={onOpenLogin}
            style={{
              width: '100%',
              background: 'linear-gradient(135deg, #38bdf8, #3b82f6)',
              color: '#ffffff',
              border: 'none',
              padding: '14px',
              borderRadius: '14px',
              fontWeight: 800,
              fontSize: '14px',
              cursor: 'pointer',
              boxShadow: '0 8px 20px rgba(56, 189, 248, 0.35)',
              transition: 'transform 0.2s ease',
            }}>
            🔑 ورود به حساب کاربری
          </button>

          <button
            onClick={onOpenRegister}
            style={{
              width: '100%',
              background: 'rgba(255, 255, 255, 0.08)',
              color: '#f8fafc',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              padding: '12px',
              borderRadius: '14px',
              fontWeight: 700,
              fontSize: '13px',
              cursor: 'pointer',
            }}>
            ✨ ثبت‌نام کاربر جدید
          </button>
        </div>
      </div>
    </div>
  )
}

export default LandingPage
