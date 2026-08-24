import {
  ArrowClockwise,
  CaretLeft,
  CaretDown,
  CaretUp,
  Check,
  CircleNotch,
  Pause,
  Play,
  SkipForward,
} from '@phosphor-icons/react'

const steps = ['Người đặt', 'VF 9', 'Vị trí', 'Showroom', 'Giờ & giữ chỗ', 'Hồ sơ', 'Xác nhận']
const toolForLog = (text) => {
  const value = String(text || '').toLowerCase()
  if (value.includes('vị trí')) return 'Lấy vị trí'
  if (value.includes('showroom')) return 'Tìm showroom'
  if (value.includes('giờ')) return 'Tìm khung giờ'
  if (value.includes('giữ chỗ')) return 'Giữ chỗ'
  if (value.includes('hồ sơ')) return 'Lưu hồ sơ'
  if (value.includes('xác nhận') || value.includes('đặt lịch thành công')) return 'Xác nhận lịch'
  if (value.includes('dọn lịch')) return 'Dọn lịch demo'
  return 'Điều khiển demo'
}

export function FloatingDemoBar({
  step = 0,
  running = false,
  paused = false,
  busy = false,
  collapsed = false,
  status = '',
  logs = [],
  onAutoPlay,
  onPause,
  onNext,
  onBack,
  onReset,
  onToggle,
}) {
  return (
    <aside className={`floating-demo-bar ${collapsed ? 'is-collapsed' : ''}`} aria-label="Điều khiển demo đặt lịch">
      <button
        type="button"
        className="floating-demo-bar__toggle"
        onClick={onToggle}
        aria-expanded={!collapsed}
        aria-label={collapsed ? 'Mở thanh demo' : 'Thu gọn thanh demo'}
      >
        <span>Demo luồng chuẩn</span>
        {collapsed ? <CaretUp size={15} weight="bold" /> : <CaretDown size={15} weight="bold" />}
      </button>

      {!collapsed && (
        <div className="floating-demo-bar__content">
          <div className="floating-demo-bar__head">
            <div>
              <span>VinFast Booking</span>
              <strong>Happy path · VF 9</strong>
            </div>
            <p aria-live="polite">{status || 'Sẵn sàng trình diễn'}</p>
          </div>

          <ol className="floating-demo-bar__steps" aria-label="Tiến trình demo">
            {steps.map((label, index) => {
              const number = index + 1
              const complete = step > number
              const active = step === number
              return (
                <li key={label} className={`${complete ? 'is-complete' : ''} ${active ? 'is-active' : ''}`}>
                  <span aria-hidden="true">{complete ? <Check size={12} weight="bold" /> : number}</span>
                  <small>{label}</small>
                </li>
              )
            })}
          </ol>

          <div className="floating-demo-bar__actions">
            <button type="button" className="floating-demo-bar__primary" onClick={running ? onPause : onAutoPlay} disabled={busy}>
              {busy ? <CircleNotch size={16} className="is-spinning" /> : running && !paused ? <Pause size={16} /> : <Play size={16} weight="fill" />}
              {running && !paused ? 'Tạm dừng' : paused ? 'Tiếp tục' : 'Tự động chạy'}
            </button>
            <button type="button" className="floating-demo-bar__icon-button" onClick={onNext} disabled={busy || (running && !paused) || step >= steps.length} aria-label="Chạy bước tiếp theo">
              <SkipForward size={17} weight="bold" />
            </button>
            <button type="button" className="floating-demo-bar__icon-button" onClick={onBack} disabled={busy || (running && !paused) || step <= 0} aria-label="Quay lại chặng trước">
              <CaretLeft size={17} weight="bold" />
            </button>
            <button type="button" className="floating-demo-bar__icon-button" onClick={onReset} disabled={busy} aria-label="Bắt đầu lại demo">
              <ArrowClockwise size={17} weight="bold" />
            </button>
          </div>

          <details className="floating-demo-bar__logs">
            <summary>Nhật ký demo <span>{logs.length}</span></summary>
            <ol aria-label="Nhật ký thực thi demo">
              {logs.length ? logs.slice().reverse().map((entry) => (
                <li key={entry.id}><time>{entry.time}</time><span><b>{toolForLog(entry.text)}</b>{entry.text}</span></li>
              )) : <li>Chưa có thao tác nào.</li>}
            </ol>
          </details>
        </div>
      )}
    </aside>
  )
}
