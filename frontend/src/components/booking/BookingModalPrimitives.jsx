/**
 * components/booking/BookingModalPrimitives.jsx
 *
 * Modals shown at the beginning of the booking flow:
 * - RecipientModal: Choice modal for self, other, or lookup
 * - ResumeModal: Choice modal for resuming an uncompleted session
 */
import { ArrowLeft, ArrowRight, CalendarBlank, Clock, User, UserPlus } from '@phosphor-icons/react'
import { useDialogFocus } from '../../hooks/useDialogFocus'

export function RecipientModal({ onSelect, onLookup, onBack }) {
  const dialogRef = useDialogFocus()

  return (
    <div
      ref={dialogRef}
      className="recipient-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="recipient-title"
      tabIndex={-1}
      onKeyDown={(event) => {
        if (event.key === 'Escape') onBack()
      }}
    >
      <div className="recipient-modal__panel">
        <button className="recipient-modal__back" type="button" onClick={onBack} aria-label="Quay lại trang vừa xem" title="Quay lại trang vừa xem">
          <ArrowLeft size={20} weight="bold" aria-hidden="true" />
        </button>
        <span className="recipient-modal__mark"><User size={24} weight="light" /></span>
        <p>Trước khi bắt đầu</p>
        <h1 id="recipient-title">Bạn muốn làm gì <span className="no-orphan">hôm nay?</span></h1>
        <div className="recipient-modal__choices">
          <button type="button" onClick={() => onSelect('self')}>
            <User size={24} weight="light" />
            <span><strong>Đặt lịch cho chính tôi</strong><small>Người đặt lịch cũng là người lái thử</small></span>
            <ArrowRight size={18} weight="light" />
          </button>
          <button type="button" onClick={() => onSelect('other')}>
            <UserPlus size={24} weight="light" />
            <span><strong>Đặt hộ người khác</strong><small>Lưu riêng thông tin người đặt và người lái</small></span>
            <ArrowRight size={18} weight="light" />
          </button>
          <button type="button" onClick={onLookup}>
            <CalendarBlank size={24} weight="light" />
            <span><strong>Tra cứu lịch đã đặt</strong><small>Xem lại, đổi giờ hoặc huỷ lịch của bạn</small></span>
            <ArrowRight size={18} weight="light" />
          </button>
        </div>
        <small>Bạn có thể thay đổi thông tin trước khi xác nhận cuối cùng.</small>
      </div>
    </div>
  )
}

export function ResumeModal({ onContinue, onRestart, onBack }) {
  const dialogRef = useDialogFocus()

  return (
    <div
      ref={dialogRef}
      className="recipient-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="resume-title"
      tabIndex={-1}
      onKeyDown={(event) => {
        if (event.key === 'Escape') onBack()
      }}
    >
      <div className="recipient-modal__panel booking-resume-modal">
        <button className="recipient-modal__back" type="button" onClick={onBack} aria-label="Về trang chủ" title="Về trang chủ">
          <ArrowLeft size={20} weight="bold" aria-hidden="true" />
        </button>
        <span className="recipient-modal__mark"><Clock size={24} weight="light" /></span>
        <p>Phiên trước chưa hoàn tất</p>
        <h1 id="resume-title">Bạn muốn tiếp tục lịch đang dở?</h1>
        <div className="recipient-modal__choices booking-resume-modal__choices">
          <button type="button" onClick={onContinue}><span><strong>Tiếp tục</strong><small>Quay lại bước bạn đang thực hiện</small></span><ArrowRight size={18} weight="light" /></button>
          <button type="button" onClick={onRestart}><span><strong>Làm mới</strong><small>Bắt đầu một lịch đặt mới</small></span><ArrowRight size={18} weight="light" /></button>
        </div>
      </div>
    </div>
  )
}
