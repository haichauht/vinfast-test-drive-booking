/**
 * components/booking/VehicleWorkspace.jsx — 3 mảnh giao diện liên quan tới MẪU XE trong luồng đặt lịch.
 *
 * ⚠️ CẢNH BÁO QUAN TRỌNG — chỉ 1 trong 3 mảnh dưới đây thực sự chạy trên web:
 * - VehicleShot     → ĐANG DÙNG (BookingSummary.jsx và BookingManagementModals.jsx import).
 * - VehicleSwitcher → KHÔNG DÙNG. BookingPage.jsx chạy bản riêng của nó (dòng ~358).
 * - VehiclePanel    → KHÔNG DÙNG. BookingPage.jsx chạy bản riêng của nó (dòng ~424).
 * Sửa VehicleSwitcher/VehiclePanel ở file này sẽ KHÔNG thấy gì đổi trên web.
 * Muốn sửa 2 mảnh đó, vào src/pages/BookingPage.jsx. Xem thêm ghi chú đầu BookingPage.jsx.
 *
 * Nội dung 3 mảnh:
 * - VehicleShot: ảnh studio của xe, gắn class theo studioShot.mode (cutout ảnh tách nền /
 *   plate / photo) để CSS chọn đúng cách đóng khung.
 * - VehicleSwitcher: hộp thoại "Bạn muốn cầm lái mẫu nào?", chia 2 nhóm theo carGroups,
 *   đóng bằng phím Esc hoặc bấm ra ngoài.
 * - VehiclePanel: thẻ "Mẫu xe đang giữ" — ảnh xe, 3 thông số đầu và link về trang chi tiết.
 *
 * Code viết dồn 1 dòng rất dài, đọc bằng cách bật word-wrap (Option+Z trong VS Code).
 * Style tương ứng: mục "Bảng chọn / đổi mẫu xe" trong index.css.
 */
import { useEffect } from 'react'
import { ArrowRight, CaretDown, Check, X } from '@phosphor-icons/react'
import { Link } from 'react-router-dom'
import { SmartImage } from '../SmartImage'
import { carGroups } from '../../data/cars'

export function VehicleShot({ car, className = '', eager = false, mode = car.studioShot.mode }) {
  return <SmartImage className={`vehicle-shot vehicle-shot--${mode} ${className}`.trim()} src={car.studioShot.src} alt={`${car.name} — ảnh studio`} eager={eager} />
}

export function VehicleSwitcher({ cars, currentId, onSelect, onClose }) {
  useEffect(() => { const close = (event) => event.key === 'Escape' && onClose(); window.addEventListener('keydown', close); return () => window.removeEventListener('keydown', close) }, [onClose])
  return <div className="vehicle-switcher" role="dialog" aria-modal="true" aria-labelledby="vehicle-switcher-title" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><div className="vehicle-switcher__panel">
    <button type="button" className="vehicle-switcher__close" onClick={onClose} aria-label="Đóng bảng chọn xe"><X size={17} weight="light" /></button>
    <header><p>Đổi mẫu xe lái thử</p><h2 id="vehicle-switcher-title">Bạn muốn cầm lái mẫu nào?</h2><small>ViVi giữ lại địa chỉ và showroom bạn đã chọn; chỉ khung giờ được mở lại để ghép đúng xe mới.</small></header>
    <div className="vehicle-switcher__body">{carGroups.map((group) => <section key={group.id}><div className="vehicle-switcher__group"><strong>{group.label}</strong><small>{group.description}</small></div><div className="vehicle-switcher__grid">{cars.filter((car) => car.category === group.id).map((car) => { const active = car.id === currentId; return <button type="button" key={car.id} className={active ? 'is-active' : ''} onClick={() => onSelect(car)} aria-pressed={active}><VehicleShot car={car} className="vehicle-switcher__shot" /><span className="vehicle-switcher__meta"><strong>{car.name}</strong><small>{car.body} · {car.seats}</small></span><span className="vehicle-switcher__state">{active ? <><Check size={13} weight="bold" /> Đang chọn</> : <>Chọn mẫu này <ArrowRight size={13} weight="light" /></>}</span></button> })}</div></section>)}</div>
  </div></div>
}

export function VehiclePanel({ car }) {
  return <section className="studio-vehicle" aria-label={`Mẫu xe ${car.name}`}><div className="studio-vehicle__ambient" aria-hidden="true" /><div className="studio-vehicle__heading"><span>Mẫu xe đang giữ</span><strong>{car.name}</strong><small>{car.body} · {car.seats}</small></div><div className="studio-vehicle__stage" key={car.id}><VehicleShot car={car} className="studio-vehicle__image" eager /></div><div className="studio-vehicle__specs">{car.specs.slice(0, 3).map((spec) => <div key={spec.label}><strong>{spec.value}</strong><span>{spec.label}</span></div>)}</div><Link to={`/models/${car.id}`}>Xem lại thông tin xe <ArrowRight size={15} weight="light" /></Link></section>
}
