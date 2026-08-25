/**
 * components/booking/BookingCustomerForm.jsx — Form nhập thông tin khách (bước 5, trong khung chat ViVi).
 *
 * ✅ ĐANG DÙNG THẬT: BookingPage.jsx import dưới tên CustomerForm.
 *
 * Form đổi hình theo prop `recipient`:
 * - recipient = 'self'  → 3 ô: Họ và tên · Email · Số điện thoại.
 * - recipient = 'other' → thêm "Tên người lái thử", 2 nhãn đổi thành
 *   "Tên người đặt lịch" / "Email nhận OTP", và MỘT KHỐI LIÊN HỆ RIÊNG cho người lái.
 *
 * KHỐI LIÊN HỆ NGƯỜI LÁI (chỉ ở nhánh đặt hộ): mặc định tick "dùng chung liên hệ với
 * người đặt". Bỏ tick thì hiện 2 ô email + SĐT riêng cho người lái. Trước đây form không
 * có phần này, nên dù đã tách TÊN thì email và SĐT vẫn bị gán chung của người đặt —
 * showroom gọi nhầm người, và người cầm lái không nhận được thông báo nào.
 *
 * Ngoài ra có 2 ô tick: xác nhận có giấy phép lái xe (BẮT BUỘC, sai thì báo lỗi đỏ)
 * và đồng ý nhận thông tin ưu đãi (mặc định đã tick sẵn).
 *
 * KHÔNG có ô tải ảnh GPLX ở đây và đừng thêm vào — chỉ cần lời cam kết.
 *
 * File này chỉ hiển thị. Toàn bộ việc kiểm tra dữ liệu và báo lỗi nằm ở hàm submitPerson()
 * trong BookingPage.jsx — muốn đổi quy tắc validate thì sửa bên đó.
 */
import { ArrowRight, Check } from '@phosphor-icons/react'

export function BookingCustomerForm({ recipient, value, errors, onChange, onSubmit, onBack }) {
  const bookingForOther = recipient === 'other'
  const shareContact = value.driverSameContact !== false

  return (
    <form className="vivi-customer-form" onSubmit={onSubmit} noValidate>
      <div className="vivi-customer-form__grid">
        <label><span>{bookingForOther ? 'Tên người đặt lịch' : 'Họ và tên'} <span style={{ color: '#ef4444' }}>*</span></span><input name="booking-name" autoComplete="name" value={value.bookingName} onChange={(event) => onChange('bookingName', event.target.value)} />{errors.bookingName && <small role="alert">{errors.bookingName}</small>}</label>
        {bookingForOther && <label><span>Tên người lái thử <span style={{ color: '#ef4444' }}>*</span></span><input name="driver-name" autoComplete="off" value={value.driverName} onChange={(event) => onChange('driverName', event.target.value)} />{errors.driverName && <small role="alert">{errors.driverName}</small>}</label>}
        <label><span>Email <span style={{ color: '#ef4444' }}>*</span></span><input name="email" type="email" inputMode="email" autoComplete="email" placeholder="tenban@example.com" value={value.email} onChange={(event) => onChange('email', event.target.value)} required />{errors.email && <small role="alert">{errors.email}</small>}</label>
        <label><span>Số điện thoại</span><input name="tel" type="tel" inputMode="tel" autoComplete="tel" placeholder="09xx xxx xxx" value={value.phone} onChange={(event) => onChange('phone', event.target.value)} />{errors.phone && <small role="alert">{errors.phone}</small>}</label>
      </div>

      {bookingForOther && (
        <fieldset className="vivi-driver-contact">
          <legend>Liên hệ của người lái thử</legend>
          <label className="license-check">
            <input
              type="checkbox"
              checked={shareContact}
              onChange={(event) => onChange('driverSameContact', event.target.checked)}
            />
            <span><Check size={14} weight="bold" /></span>
            <p>{value.driverName?.trim() || 'Người lái thử'} dùng chung <strong>email và số điện thoại</strong> với tôi.</p>
          </label>

          {!shareContact && (
            <>
              <p className="vivi-driver-contact__note">
                Showroom sẽ liên hệ trực tiếp với người lái theo thông tin dưới đây.
              </p>
              <div className="vivi-customer-form__grid">
                <label><span>Email người lái <span style={{ color: '#ef4444' }}>*</span></span><input name="driver-email" type="email" inputMode="email" autoComplete="off" placeholder="nguoilai@example.com" value={value.driverEmail} onChange={(event) => onChange('driverEmail', event.target.value)} />{errors.driverEmail && <small role="alert">{errors.driverEmail}</small>}</label>
                <label><span>Số điện thoại người lái</span><input name="driver-phone" type="tel" inputMode="tel" autoComplete="off" placeholder="09xx xxx xxx" value={value.driverPhone} onChange={(event) => onChange('driverPhone', event.target.value)} />{errors.driverPhone && <small role="alert">{errors.driverPhone}</small>}</label>
              </div>
            </>
          )}
        </fieldset>
      )}
      <label className={`license-check ${errors.hasLicense ? 'has-error' : ''}`}><input type="checkbox" checked={value.hasLicense} onChange={(event) => onChange('hasLicense', event.target.checked)} /><span><Check size={14} weight="bold" /></span><p>Tôi xác nhận người lái thử <strong>có giấy phép lái xe</strong> phù hợp với mẫu xe đăng ký <span style={{ color: '#ef4444' }}>*</span>.</p></label>
      {errors.hasLicense && <small className="vivi-customer-form__license-error" role="alert">{errors.hasLicense}</small>}
      <label className="license-check"><input type="checkbox" checked={value.marketingConsent} onChange={(event) => onChange('marketingConsent', event.target.checked)} /><span><Check size={14} weight="bold" /></span><p>Tôi đồng ý nhận <strong>thông tin ưu đãi</strong>, <strong>khuyến mãi</strong> và <strong>sự kiện mới nhất</strong> từ VinFast.</p></label>
      {/* Cặp nút đi liền nhau, đúng như màn xem lại phiếu (.vivi-review-actions): nút chính
          bên trái, lối lùi bên phải. Trước đây bước này chỉ có mỗi nút chính nên vào tới form
          là kẹt — muốn đổi khung giờ phải tự mò sang bảng bên trái.

          Nhãn "Chỉnh lại thông tin" là chữ anh Minh chọn, dùng chung với nút cùng vai ở màn xem
          lại phiếu. Nút đưa về bảng lịch bên trái, nơi đổi được khung giờ / showroom / mẫu xe —
          tức mọi lựa chọn đã chốt TRƯỚC bước điền form này. */}
      <div className="vivi-customer-form__actions">
        <button type="submit">Tạo phiếu để kiểm tra <ArrowRight size={16} weight="light" /></button>
        {onBack && (
          <button type="button" onClick={onBack}>Hủy</button>
        )}
      </div>
    </form>
  )
}
