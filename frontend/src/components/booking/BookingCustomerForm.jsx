/**
 * components/booking/BookingCustomerForm.jsx — Form nhập thông tin khách (bước 5, trong khung chat ViVi).
 *
 * ✅ ĐANG DÙNG THẬT: BookingPage.jsx import dưới tên CustomerForm.
 *
 * Form đổi hình theo prop `recipient`:
 * - recipient = 'self'  → 3 ô: Họ và tên · Email · Số điện thoại.
 * - recipient = 'other' → 4 ô: thêm "Tên người lái thử", và 2 nhãn đổi thành
 *   "Tên người đặt lịch" / "Email nhận OTP".
 *
 * Ngoài ra có 2 ô tick: xác nhận có giấy phép lái xe (BẮT BUỘC, sai thì báo lỗi đỏ)
 * và đồng ý nhận thông tin ưu đãi (mặc định đã tick sẵn).
 *
 * File này chỉ hiển thị. Toàn bộ việc kiểm tra dữ liệu và báo lỗi nằm ở hàm submitPerson()
 * trong BookingPage.jsx (~dòng 1401) — muốn đổi quy tắc validate thì sửa bên đó.
 */
import { ArrowRight, Check } from '@phosphor-icons/react'

export function BookingCustomerForm({ recipient, value, errors, onChange, onSubmit }) {
  return (
    <form className="vivi-customer-form" onSubmit={onSubmit} noValidate>
      <div className="vivi-customer-form__grid">
        <label><span>{recipient === 'other' ? 'Tên người đặt lịch' : 'Họ và tên'} <span style={{ color: '#ef4444' }}>*</span></span><input value={value.bookingName} onChange={(event) => onChange('bookingName', event.target.value)} />{errors.bookingName && <small role="alert">{errors.bookingName}</small>}</label>
        {recipient === 'other' && <label><span>Tên người lái thử <span style={{ color: '#ef4444' }}>*</span></span><input value={value.driverName} onChange={(event) => onChange('driverName', event.target.value)} />{errors.driverName && <small role="alert">{errors.driverName}</small>}</label>}
        <label><span>Email <span style={{ color: '#ef4444' }}>*</span></span><input type="email" placeholder="tenban@example.com" value={value.email} onChange={(event) => onChange('email', event.target.value)} required />{errors.email && <small role="alert">{errors.email}</small>}</label>
        <label><span>Số điện thoại</span><input type="tel" placeholder="09xx xxx xxx" value={value.phone} onChange={(event) => onChange('phone', event.target.value)} />{errors.phone && <small role="alert">{errors.phone}</small>}</label>
      </div>
      <label className={`license-check ${errors.hasLicense ? 'has-error' : ''}`}><input type="checkbox" checked={value.hasLicense} onChange={(event) => onChange('hasLicense', event.target.checked)} /><span><Check size={14} weight="bold" /></span><p>Tôi xác nhận người lái thử <strong>có giấy phép lái xe</strong> phù hợp với mẫu xe đăng ký <span style={{ color: '#ef4444' }}>*</span>.</p></label>
      {errors.hasLicense && <small className="vivi-customer-form__license-error" role="alert">{errors.hasLicense}</small>}
      <label className="license-check" style={{ marginTop: '12px' }}><input type="checkbox" checked={value.marketingConsent} onChange={(event) => onChange('marketingConsent', event.target.checked)} /><span><Check size={14} weight="bold" /></span><p>Tôi đồng ý nhận <strong>thông tin ưu đãi</strong>, <strong>khuyến mãi</strong> và <strong>sự kiện mới nhất</strong> từ VinFast.</p></label>
      <button type="submit">Tạo phiếu để kiểm tra <ArrowRight size={16} weight="light" /></button>
    </form>
  )
}
