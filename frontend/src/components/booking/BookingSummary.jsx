/**
 * components/booking/BookingSummary.jsx — Bảng chọn khung giờ và Phiếu đặt lịch.
 *
 * ✅ ĐANG DÙNG THẬT: BookingPage.jsx import cả 2 component bên dưới.
 *
 * - SchedulePanel: lưới lịch trống (bước 4). Mỗi thẻ là một ngày, bên trong là các khung giờ.
 *   Khung giờ đang chọn nhận class .is-active. Lịch do backend trả về, không tự sinh.
 *
 * - BookingTicket: phiếu đặt lịch, dùng ở HAI nơi với giao diện hơi khác nhau —
 *   màn xem lại trước khi đặt (chưa có bookingCode) và màn thành công (prop compact + có mã lịch).
 *   Gồm ảnh xe, 8 dòng thông tin và dòng xác nhận đã có giấy phép lái xe.
 *
 * ⚠️ Còn dữ liệu giả: bảng tên/số điện thoại tư vấn viên hard-code ở dòng ~9 (staff).
 *   Chỉ dùng khi backend chưa trả showroom.staff — khi nối xong nên xoá hẳn bảng này.
 *
 * Style tương ứng: .studio-schedule và .studio-ticket trong index.css.
 */
import { CalendarBlank, CheckCircle, Clock } from '@phosphor-icons/react'
import { VehicleShot } from './VehicleWorkspace'

export function SchedulePanel({ car, showroom, slots, pendingSlot, onPick }) {
  return <section className="studio-schedule" aria-label="Lịch lái thử còn trống"><div className="studio-schedule__heading"><span>Lịch có đúng mẫu xe</span><h2>{car.name} tại {showroom.name}</h2><p>Mỗi khung giờ bên dưới đã được ghép với xe lái thử đang sẵn sàng.</p></div><div className="studio-schedule__grid">{slots.map((day) => <article key={day.value}><header><CalendarBlank size={18} weight="light" /><strong>{day.dateLabel}</strong></header><div>{day.times.map((entry) => <button type="button" className={pendingSlot?.slotId === entry.slotId ? 'is-active' : ''} key={entry.slotId} onClick={() => onPick({ date: day.value, dateLabel: day.dateLabel, time: entry.time, slotId: entry.slotId })}><Clock size={15} weight="light" /> {entry.time}</button>)}</div></article>)}</div></section>
}

export function BookingTicket({ car, showroom, slot, person, recipient, bookingCode, compact = false }) {
  const staff = { sr_hanoi: ['Nguyễn Văn Hùng', '0911 111 111'], sr_hcm: ['Trần Thị Lan', '0922 222 222'], sr_danang: ['Lê Hoàng Nam', '0933 333 333'], sr_smart_city: ['Phạm Văn Minh', '0944 444 444'], sr_royal_city: ['Hoàng Thuỳ Linh', '0955 555 555'], sr_mydinh: ['Đỗ Anh Tuấn', '0966 666 666'], sr_ocean_park: ['Bùi Quốc Anh', '0977 777 777'], sr_tayho: ['Vũ Thị Hà', '0988 888 888'] }[showroom.id] || ['Nguyễn Văn Hùng', '0911 111 111']
  const rows = [['Người đặt lịch', person.bookingName], ['Người lái thử', recipient === 'other' ? person.driverName : person.bookingName], ['Điện thoại', person.phone], ['Email', person.email || 'Không đăng ký nhận email'], ['Mẫu xe', car.name], ['Showroom', showroom.name], ['Thời gian', `${slot.time} · ${slot.dateLabel}`], ['Tư vấn viên', `${showroom.staff || staff[0]} · ${showroom.staffPhone || staff[1]}`]]
  return <section className={`studio-ticket ${compact ? 'studio-ticket--compact' : ''}`}><header><span>{bookingCode ? 'Lịch lái thử đã xác nhận' : 'Kiểm tra trước khi đặt lịch'}</span>{bookingCode && <strong>{bookingCode}</strong>}</header><div className="studio-ticket__vehicle"><VehicleShot car={car} /><span><strong>{car.name}</strong><small>{car.body}</small></span></div><dl>{rows.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl><p><CheckCircle size={16} weight="fill" /> Đã xác nhận có giấy phép lái xe phù hợp.</p></section>
}
