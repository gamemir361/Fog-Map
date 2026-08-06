export function TrackingConfirmModal({ isOpen, onClose, onConfirm }) {
  if (!isOpen) return null

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        backdropFilter: 'blur(8px)',
        zIndex: 3500,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
        fontFamily: 'Vazirmatn, sans-serif',
      }}>
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '420px',
          padding: '24px',
          borderRadius: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
        }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              borderRadius: '12px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '20px',
              color: '#ef4444',
            }}>
            ⚠️
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 800, color: 'var(--text-main)' }}>
              آیا از غیرفعال‌سازی ردیابی کاوش اطمینان دارید؟
            </h3>
            <span style={{ fontSize: '11px', color: 'var(--text-sub)' }}>Disable Exploration Tracking?</span>
          </div>
        </div>

        {/* Warning Bullet List */}
        <div style={{ background: 'rgba(125, 125, 125, 0.1)', padding: '14px', borderRadius: '12px', fontSize: '12px', color: 'var(--text-main)', lineHeight: 1.7 }}>
          <p style={{ margin: '0 0 8px 0', fontWeight: 700, color: '#f87171' }}>در زمان غیرفعال بودن:</p>
          <ul style={{ margin: 0, paddingRight: '18px' }}>
            <li>مناطق جدید ثبت نخواهند شد. (New areas will NOT be recorded)</li>
            <li>درصد پیشرفت کاوش افزایش نمی‌یابد. (Exploration percentage will NOT increase)</li>
            <li>امتیاز XP دریافت نخواهید کرد. (XP will NOT be earned)</li>
            <li>دستاوردها پیشرفت نخواهند کرد. (Achievements will NOT progress)</li>
          </ul>
          <p style={{ margin: '10px 0 0 0', fontSize: '11px', color: 'var(--text-sub)' }}>
            اطلاعات کاوش قبلی شما محفوظ خواهد ماند و در هر زمان قابل ازسرگیری است.
          </p>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '4px' }}>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(125, 125, 125, 0.15)',
              border: '1px solid var(--panel-border)',
              color: 'var(--text-main)',
              padding: '10px 16px',
              borderRadius: '10px',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
            }}>
            انصراف (Cancel)
          </button>
          <button
            onClick={() => {
              onConfirm()
              onClose()
            }}
            style={{
              background: 'linear-gradient(135deg, #ef4444, #dc2626)',
              border: 'none',
              color: '#ffffff',
              padding: '10px 18px',
              borderRadius: '10px',
              fontSize: '12px',
              fontWeight: 800,
              cursor: 'pointer',
              boxShadow: '0 4px 14px rgba(239, 68, 68, 0.4)',
            }}>
            غیرفعال‌سازی ردیابی (Disable Tracking)
          </button>
        </div>
      </div>
    </div>
  )
}

export default TrackingConfirmModal
