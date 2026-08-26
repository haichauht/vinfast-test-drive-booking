import {
  CaretDown,
  CaretLeft,
  CaretRight,
  CaretUp,
  Check,
  CircleNotch,
  DotsThreeVertical,
  Pause,
  Play,
  X,
} from '@phosphor-icons/react'
import { useRef } from 'react'

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
  position = null,
  logs = [],
  onAutoPlay,
  onPause,
  onNext,
  onBack,
  onExit,
  onToggle,
  onPositionChange,
}) {
  const dragRef = useRef(null)
  const justDraggedRef = useRef(false)

  const startDrag = (event) => {
    if (!collapsed) return
    const rect = event.currentTarget.closest('.floating-demo-bar')?.getBoundingClientRect()
    if (!rect) return
    justDraggedRef.current = false
    dragRef.current = { pointerId: event.pointerId, offsetX: event.clientX - rect.left, offsetY: event.clientY - rect.top, startX: event.clientX, startY: event.clientY }
    event.currentTarget.setPointerCapture?.(event.pointerId)
  }

  const moveDrag = (event) => {
    const drag = dragRef.current
    if (!drag || drag.pointerId !== event.pointerId) return
    const panel = event.currentTarget.closest('.floating-demo-bar')
    if (!panel) return
    const width = panel.getBoundingClientRect().width
    const height = panel.getBoundingClientRect().height
    const left = Math.max(8, Math.min(window.innerWidth - width - 8, event.clientX - drag.offsetX))
    const top = Math.max(8, Math.min(window.innerHeight - height - 8, event.clientY - drag.offsetY))
    if (Math.abs(event.clientX - drag.startX) > 4 || Math.abs(event.clientY - drag.startY) > 4) justDraggedRef.current = true
    onPositionChange?.({
      left,
      top,
      width,
      side: left + (width / 2) < window.innerWidth / 2 ? 'left' : 'right',
    })
  }

  const endDrag = (event) => {
    if (dragRef.current?.pointerId !== event.pointerId) return
    event.currentTarget.releasePointerCapture?.(event.pointerId)
    dragRef.current = null
  }

  const toggle = () => {
    if (justDraggedRef.current) {
      justDraggedRef.current = false
      return
    }
    onToggle()
  }

  const primaryAction = running ? onPause : onAutoPlay
  const primaryLabel = running && !paused ? 'Tạm dừng' : paused ? 'Tiếp tục' : 'Tự động chạy'
  const primaryIcon = busy ? <CircleNotch size={16} className="is-spinning" /> : running && !paused ? <Pause size={16} /> : <Play size={16} weight="fill" />
  const disableStepControls = busy || (running && !paused)

  const positionedStyle = position
    ? (position.side === 'left'
      ? { left: position.left, top: position.top, right: 'auto', bottom: 'auto' }
      : { right: Math.max(8, window.innerWidth - position.left - position.width), top: position.top, left: 'auto', bottom: 'auto' })
    : undefined

  return (
    <aside className={`floating-demo-bar ${collapsed ? 'is-collapsed' : ''} ${position?.side === 'left' ? 'is-anchored-left' : position?.side === 'right' ? 'is-anchored-right' : ''}`} style={positionedStyle} aria-label="Điều khiển demo đặt lịch mô phỏng">
      {collapsed ? (
        <div className="floating-demo-bar__compact-actions">
          <button type="button" className="floating-demo-bar__primary floating-demo-bar__primary--compact" onClick={primaryAction} disabled={busy}>
            {primaryIcon}
            <span>{running && !paused ? 'Dừng' : paused ? 'Tiếp' : 'Bắt đầu'}</span>
          </button>
          <button type="button" className="floating-demo-bar__icon-button" onClick={onBack} disabled={disableStepControls || step <= 0} aria-label="Quay lại chặng trước" title="Quay lại chặng trước"><CaretLeft size={16} weight="bold" /></button>
          <button type="button" className="floating-demo-bar__icon-button" onClick={onNext} disabled={disableStepControls || step >= steps.length} aria-label="Chạy bước tiếp theo" title="Chạy bước tiếp theo"><CaretRight size={16} weight="bold" /></button>
          <button type="button" className="floating-demo-bar__toggle" onClick={toggle} aria-expanded="false" aria-label="Mở rộng bảng điều khiển demo" title="Mở rộng bảng điều khiển demo"><CaretUp size={15} weight="bold" /></button>
          <button type="button" className="floating-demo-bar__compact-exit" onClick={onExit} disabled={busy} aria-label="Thoát chế độ demo" title="Thoát chế độ demo"><X size={15} weight="bold" /></button>
          <button
            type="button"
            className="floating-demo-bar__drag-handle"
            onPointerDown={startDrag}
            onPointerMove={moveDrag}
            onPointerUp={endDrag}
            onPointerCancel={endDrag}
            aria-label="Giữ và kéo để đổi vị trí"
            title="Giữ và kéo để đổi vị trí"
          >
            <DotsThreeVertical size={16} weight="bold" />
          </button>
        </div>
      ) : (
        <div className="floating-demo-bar__panel-actions">
          <button type="button" className="floating-demo-bar__toggle" onClick={toggle} aria-expanded="true" aria-label="Thu gọn bảng điều khiển demo" title="Thu gọn bảng điều khiển demo"><CaretDown size={15} weight="bold" /></button>
          <button type="button" className="floating-demo-bar__exit" onClick={onExit} disabled={busy} aria-label="Thoát chế độ demo" title="Thoát chế độ demo"><X size={15} weight="bold" /></button>
        </div>
      )}

      {!collapsed && (
        <div className="floating-demo-bar__content">
          <div className="floating-demo-bar__head">
            <div>
              <span>Chế độ demo</span>
              <strong>VF 9 · Không tạo lịch thật</strong>
            </div>
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
            <button type="button" className="floating-demo-bar__primary" onClick={primaryAction} disabled={busy}>
              {primaryIcon}
              {primaryLabel}
            </button>
            <button type="button" className="floating-demo-bar__icon-button" onClick={onBack} disabled={disableStepControls || step <= 0} aria-label="Quay lại chặng trước" title="Quay lại chặng trước">
              <CaretLeft size={16} weight="bold" />
            </button>
            <button type="button" className="floating-demo-bar__icon-button" onClick={onNext} disabled={disableStepControls || step >= steps.length} aria-label="Chạy bước tiếp theo" title="Chạy bước tiếp theo">
              <CaretRight size={16} weight="bold" />
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
