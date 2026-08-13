/**
 * pages/BookingPage.jsx — TRANG ĐẶT LỊCH LÁI THỬ tại /booking. File lớn nhất dự án (~1800 dòng).
 *
 * Đây là trái tim của sản phẩm: khung chat ViVi bên phải, không gian làm việc bên trái,
 * và một máy trạng thái (state machine) điều khiển toàn bộ luồng.
 *
 * ══ LUỒNG 9 BƯỚC (biến `stage`) ══
 *  idle → chọn đặt cho ai (RecipientModal)  ·  need_car → chọn mẫu xe
 *  need_address / need_ward → nhập địa chỉ hoặc bấm lấy GPS
 *  choose_showroom → chọn showroom trên bản đồ  ·  choose_slot → chọn khung giờ
 *  collect_info → điền thông tin  ·  review → xem lại phiếu  ·  success → đặt xong, có mã lịch
 *  Ngoài luồng chính còn nhánh 'lookup' để tra cứu/sửa/huỷ lịch cũ bằng OTP.
 *  Vào từ /booking?car=vf9 thì bỏ qua bước chọn xe.
 *
 * ══ 3 TAB CỦA KHÔNG GIAN LÀM VIỆC (biến `activeView`) ══
 *  'car' Mẫu xe (bấm lần nữa để mở bảng đổi xe) · 'map' Bản đồ showroom · 'schedule' Lịch.
 *  Nút "Ẩn bảng" thu gọn workspace, nút "Hiện bảng" nổi bên trái để mở lại.
 *
 * ⚠️ ══ ĐIỀU PHẢI BIẾT TRƯỚC KHI SỬA GIAO DIỆN ══
 *  Bên backend đã tách một số phần ra components/booking/, NHƯNG file này vẫn giữ bản sao
 *  cũ của nhiều component. Hai bản tồn tại song song, và bản đang chạy thật là:
 *
 *   ĐANG CHẠY từ components/booking/ — sửa ở file riêng:
 *     · ShowroomMap (import tên BookingShowroomMap) · BookingCustomerForm
 *     · SchedulePanel + BookingTicket (BookingSummary.jsx) · BookingAccessPanel
 *     · CancellationConfirmModal + RescheduleConfirmModal
 *
 *   ĐANG CHẠY từ CHÍNH FILE NÀY — sửa ngay tại đây:
 *     · RecipientModal (~239) · AgentMessage (~264) · ViViAvatar (~287)
 *     · ContextualChoices (~295) · VehicleShot (~347) · VehicleSwitcher (~358) · VehiclePanel (~424)
 *
 *   CODE CHẾT, sửa vào cũng không thấy gì đổi:
 *     · ShowroomMap bản cũ trong file này (~446–634) — đã thay bằng bản import.
 *     · Cả file components/booking/BookingChatPrimitives.jsx — không ai import.
 *     · VehicleSwitcher + VehiclePanel trong components/booking/VehicleWorkspace.jsx.
 *
 * ══ CÁC HÀM CHÍNH (theo thứ tự người dùng bấm) ══
 *  beginConversation(~1056) chọn đặt cho ai · chooseCar(~1077) / switchCar(~1092) chọn & đổi xe
 *  requestUserLocation(~753) lấy GPS · loadShowrooms(~967) tìm showroom · chooseShowroom(~1125)
 *  chooseSlot(~1149) mở popup giờ · confirmSlot(~1154) GIỮ CHỖ và bật đếm ngược
 *  submitPerson(~1401) kiểm tra form · submitBooking(~1428) chốt đặt lịch
 *  Sau response thành công: BookingSuccessCinematic chạy trước, rồi mới set stage success.
 *  handlePrompt(~1186) xử lý khi người dùng gõ tin nhắn tự do cho ViVi
 *  applyAgentToolResult(~812) — hàm khó nhất: dịch kết quả backend trả về thành trạng thái giao diện
 *  Nhánh OTP: requestAccessOtp(~1247) · verifyAccessOtp(~1267) · saveAccessProfile(~1299)
 *             confirmCancellation(~1320) · holdReschedule(~1352) · confirmReschedule(~1363)
 *
 * ══ CÒN DỮ LIỆU GIẢ ══
 *  showroomDirectory (~68): 12 showroom hard-code kèm toạ độ x/y và tên nhân viên sale.
 *  Nay backend đã trả showroom thật; mảng này chỉ còn dùng để đoán tỉnh/thành từ chữ người
 *  dùng gõ. Đừng tin cột `staff` trong đó.
 *
 * ══ SỬA GIAO DIỆN Ở ĐÂU ══
 *  Style: mục "Booking experience" và "Agent-first booking studio" trong index.css.
 *  Riêng nút "Hiện bảng" (~1498) và nút đóng workspace viết inline style ngay trong file.
 *  Trang này KHÔNG dùng AppShell — header riêng, gọn hơn, ở ~dòng 1488.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  CalendarBlank,
  CarProfile,
  CaretDown,
  Check,
  CheckCircle,
  Clock,
  Crosshair,
  MagnifyingGlass,
  MapPin,
  Minus,
  NavigationArrow,
  PaperPlaneTilt,
  Plus,
  User,
  UserPlus,
  X,
} from '@phosphor-icons/react'
import { Brand } from '../components/Brand'
import { SmartImage } from '../components/SmartImage'
import { carGroups } from '../data/cars'
import { useVehicleCatalog } from '../hooks/useSiteData'
import { viviAvatar } from '../data/media'
import { commonMedia } from '../media/assets'
import {
  confirmHeldBooking,
  cancelVerifiedBooking,
  confirmVerifiedReschedule,
  holdBookingSlot,
  holdVerifiedReschedule,
  getVerifiedBooking,
  listVerifiedBookings,
  requestBookingAccess,
  saveBookingCustomer,
  sendBookingMessage,
  searchBookingOptions,
  updateVerifiedBooking,
  verifyBookingAccess,
} from '../api/booking'
import { CHAT_MESSAGE_MAX_LENGTH } from '../api/contracts'
import { actionId } from '../api/ids'
import { useBackendStatus } from '../context/BackendStatusContext'
import { BookingCustomerForm as CustomerForm } from '../components/booking/BookingCustomerForm'
import { ShowroomMap as BookingShowroomMap } from '../components/booking/ShowroomMap'
import { BookingTicket, SchedulePanel } from '../components/booking/BookingSummary'
import { BookingAccessPanel } from '../components/booking/BookingAccessPanel'
import { CancellationConfirmModal, RescheduleConfirmModal } from '../components/booking/BookingManagementModals'
import { BookingSuccessVehicleModel, preloadVehicle3dRuntime } from '../components/Vehicle3DExperience'
import { BookingSuccessCinematic } from '../components/BookingSuccessCinematic'
import { getVehicle3dModel } from '../data/vehicle3d'

const vinfastLogo = commonMedia.vinfastLogo
const driveCars = []
const BOOKING_UI_STATE_KEY = 'vinfast:booking-ui-state'
const normalizeVehicleName = (value = '') => value.toLowerCase().replace(/^vinfast\s+/, '').replace(/[^a-z0-9]/g, '')

const readBookingUiState = () => {
  try {
    const value = window.sessionStorage.getItem(BOOKING_UI_STATE_KEY)
    return value ? JSON.parse(value) : {}
  } catch {
    return {}
  }
}

const isSensitiveChatText = (value) => /(?:\b(?:0|\+84)\d[\d\s.-]{7,}\b|\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b|\b\d{6}\b)/.test(value)

const formatDistance = (distance) => (
  Number.isFinite(distance) ? `${String(distance).replace('.', ',')} km` : ''
)

// BACKEND HANDOFF: This file is currently a complete frontend prototype/state
// machine with deterministic fixtures. Replace each TODO [BACKEND/*] boundary,
// not the visual components. Canonical contracts and failure behaviour live in
// ../../BACKEND_HANDOFF.md.

// ĐÃ XONG — KHÔNG CÒN CẦN NỐI GÌ Ở ĐÂY.
// Showroom hiện lấy thật từ backend qua searchBookingOptions() (POST /api/v1/chat với
// action=search_options), có toạ độ thật và khoảng cách do backend tính.
//
// ⚠️ MẢNG DƯỚI ĐÂY LÀ CODE CHẾT: khai báo nhưng không dòng nào trong file tham chiếu tới
// (đã kiểm bằng đếm số lần xuất hiện: chỉ đúng 1 chỗ khai báo). Giữ lại để đối chiếu tên
// showroom và toạ độ x/y cũ khi cần, KHÔNG được dùng làm dữ liệu hiển thị — cột `staff`
// và `staffPhone` trong này là tên bịa, tư vấn viên thật chỉ có sau khi booking được tạo.
// Xoá được an toàn khi không ai cần đối chiếu nữa.
const showroomDirectory = [
  {
    id: 'hcm-nguyen-thi-thap',
    province: 'TP. Hồ Chí Minh',
    name: 'VinFast Nguyễn Thị Thập',
    address: '481 Nguyễn Thị Thập, phường Tân Hưng, TP. Hồ Chí Minh',
    distance: 3.8,
    x: 25,
    y: 62,
    staff: 'Trần Gia Huy',
    staffPhone: '0908 642 731',
    models: driveCars.map((car) => car.id),
  },
  {
    id: 'hcm-thu-duc',
    province: 'TP. Hồ Chí Minh',
    name: 'VinFast Thủ Đức',
    address: '50 Lê Văn Việt, phường Tăng Nhơn Phú, TP. Hồ Chí Minh',
    distance: 7.2,
    x: 72,
    y: 30,
    staff: 'Nguyễn Hoàng Nam',
    staffPhone: '0932 184 609',
    models: driveCars.map((car) => car.id),
  },
  {
    id: 'hcm-quang-trung',
    province: 'TP. Hồ Chí Minh',
    name: 'VinFast Quang Trung',
    address: '672 Quang Trung, phường Thông Tây Hội, TP. Hồ Chí Minh',
    distance: 9.6,
    x: 46,
    y: 24,
    staff: 'Lê Thanh Vân',
    staffPhone: '0917 563 248',
    models: driveCars.map((car) => car.id),
  },
  {
    id: 'hcm-phu-nhuan',
    province: 'TP. Hồ Chí Minh',
    name: 'VinFast Phan Đăng Lưu',
    address: '216 Phan Đăng Lưu, phường Cầu Kiệu, TP. Hồ Chí Minh',
    distance: 11.4,
    x: 55,
    y: 52,
    staff: 'Phạm Khánh An',
    staffPhone: '0903 771 526',
    models: driveCars.map((car) => car.id),
  },
  {
    id: 'hn-cau-giay',
    province: 'Hà Nội',
    name: 'VinFast Cầu Giấy',
    address: '68 Nguyễn Văn Huyên, phường Nghĩa Đô, Hà Nội',
    distance: 2.9,
    x: 28,
    y: 34,
    staff: 'Đỗ Minh Quân',
    staffPhone: '0986 431 275',
    models: driveCars.map((car) => car.id),
  },
  {
    id: 'hn-ha-dong',
    province: 'Hà Nội',
    name: 'VinFast Hà Đông',
    address: '8 Quang Trung, phường Hà Đông, Hà Nội',
    distance: 8.4,
    x: 67,
    y: 64,
    staff: 'Vũ Hải Anh',
    staffPhone: '0912 805 463',
    models: driveCars.map((car) => car.id),
  },
  {
    id: 'hn-long-bien',
    province: 'Hà Nội',
    name: 'VinFast Long Biên',
    address: '7 Nguyễn Văn Linh, phường Phúc Lợi, Hà Nội',
    distance: 10.2,
    x: 72,
    y: 25,
    staff: 'Ngô Anh Dũng',
    staffPhone: '0963 284 715',
    models: driveCars.map((car) => car.id),
  },
  {
    id: 'hn-my-dinh',
    province: 'Hà Nội',
    name: 'VinFast Mỹ Đình',
    address: '2 Lê Đức Thọ, phường Từ Liêm, Hà Nội',
    distance: 11.8,
    x: 48,
    y: 58,
    staff: 'Tạ Quang Huy',
    staffPhone: '0936 517 804',
    models: driveCars.map((car) => car.id),
  },
  {
    id: 'dn-nguyen-van-linh',
    province: 'Đà Nẵng',
    name: 'VinFast Nguyễn Văn Linh',
    address: '43 Nguyễn Văn Linh, phường Hải Châu, Đà Nẵng',
    distance: 4.1,
    x: 52,
    y: 46,
    staff: 'Hồ Nhật Minh',
    staffPhone: '0905 347 812',
    models: driveCars.map((car) => car.id),
  },
  {
    id: 'dn-ngo-quyen',
    province: 'Đà Nẵng',
    name: 'VinFast Ngô Quyền',
    address: '910 Ngô Quyền, phường An Hải, Đà Nẵng',
    distance: 6.3,
    x: 68,
    y: 29,
    staff: 'Trương Hải Yến',
    staffPhone: '0914 736 205',
    models: driveCars.map((car) => car.id),
  },
  {
    id: 'dn-lien-chieu',
    province: 'Đà Nẵng',
    name: 'VinFast Liên Chiểu',
    address: '168 Tôn Đức Thắng, phường Hòa Khánh, Đà Nẵng',
    distance: 9.1,
    x: 27,
    y: 65,
    staff: 'Đinh Quốc Việt',
    staffPhone: '0905 618 374',
    models: driveCars.map((car) => car.id),
  },
  {
    id: 'bd-di-an',
    province: 'Bình Dương',
    name: 'VinFast Dĩ An',
    address: '88 GS1, phường Đông Hòa, Bình Dương',
    distance: 5.7,
    x: 48,
    y: 42,
    staff: 'Bùi Quốc Bảo',
    staffPhone: '0974 265 819',
    models: driveCars.map((car) => car.id),
  },
  {
    id: 'bd-thu-dau-mot',
    province: 'Bình Dương',
    name: 'VinFast Thủ Dầu Một',
    address: '1 Đại lộ Bình Dương, phường Phú Thọ, Bình Dương',
    distance: 8.6,
    x: 30,
    y: 31,
    staff: 'Phan Tuấn Kiệt',
    staffPhone: '0978 315 642',
    models: driveCars.map((car) => car.id),
  },
  {
    id: 'bd-thuan-an',
    province: 'Bình Dương',
    name: 'VinFast Thuận An',
    address: '32 Quốc lộ 13, phường Lái Thiêu, Bình Dương',
    distance: 10.4,
    x: 71,
    y: 65,
    staff: 'Mai Khánh Vy',
    staffPhone: '0909 427 186',
    models: driveCars.map((car) => car.id),
  },
]

function RecipientModal({ onSelect }) {
  return (
    <div className="recipient-modal" role="dialog" aria-modal="true" aria-labelledby="recipient-title">
      <div className="recipient-modal__panel">
        <span className="recipient-modal__mark"><User size={24} weight="light" /></span>
        <p>Trước khi bắt đầu</p>
        <h1 id="recipient-title">Bạn đặt lịch lái thử <span className="no-orphan">cho ai?</span></h1>
        <div className="recipient-modal__choices">
          <button type="button" onClick={() => onSelect('self')}>
            <User size={24} weight="light" />
            <span><strong>Cho chính tôi</strong><small>Người đặt lịch cũng là người lái thử</small></span>
            <ArrowRight size={18} weight="light" />
          </button>
          <button type="button" onClick={() => onSelect('other')}>
            <UserPlus size={24} weight="light" />
            <span><strong>Đặt hộ người khác</strong><small>Lưu riêng thông tin người đặt và người lái</small></span>
            <ArrowRight size={18} weight="light" />
          </button>
        </div>
        <small>Bạn có thể thay đổi thông tin trước khi xác nhận cuối cùng.</small>
      </div>
    </div>
  )
}

function ResumeModal({ onContinue, onRestart }) {
  return (
    <div className="recipient-modal" role="dialog" aria-modal="true" aria-labelledby="resume-title">
      <div className="recipient-modal__panel booking-resume-modal">
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

function AgentMessage({ message }) {
  const formatText = (text) => {
    if (!text) return null
    return text.split('\n').map((line, i) => {
      const html = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      return (
        <span
          key={i}
          style={{ display: 'block', minHeight: '1em' }}
          dangerouslySetInnerHTML={{ __html: html }}
        />
      )
    })
  }

  return (
    <div className={`vivi-message vivi-message--${message.role}`}>
      {message.role === 'assistant' && <ViViAvatar compact />}
      <div><p>{formatText(message.text)}</p></div>
    </div>
  )
}

function ViViAvatar({ compact = false }) {
  return (
    <span className={`${compact ? 'vivi-message__avatar' : 'vivi-studio__avatar'} vivi-avatar`}>
      <img src={viviAvatar} alt="" aria-hidden="true" />
    </span>
  )
}

function ContextualChoices({ stage, car, locationSuggestions, showrooms, slots, onResolveArea, onShowroom, onSlot }) {
  if (!car) return null

  if (stage === 'need_address' || stage === 'need_ward') {
    return null
  }

  if (stage === 'choose_showroom' && showrooms.length) {
    return (
      <div className="agent-context" aria-label="Chọn showroom trong cuộc trò chuyện">
        <div className="agent-context__heading"><span>Showroom phù hợp</span><small>Đã ưu tiên có xe trước, khoảng cách sau</small></div>
        <div className="agent-context__rail">
          {showrooms.slice(0, 4).map((showroom) => (
            <button type="button" key={showroom.id} onClick={() => onShowroom(showroom)}>
              <span><MapPin size={16} weight="light" /></span>
              <strong>{showroom.name.replace('VinFast ', '')}</strong>
              <small>{formatDistance(showroom.distance) ? `${formatDistance(showroom.distance)} · ` : ''}Có {car.name}</small>
            </button>
          ))}
        </div>
      </div>
    )
  }

  if (stage === 'choose_slot' && slots.length) {
    // Quick choices must mirror the calendar's inventory state. Never surface a
    // held/booked cell in chat as if it could be selected.
    const quickSlots = slots.flatMap((day) => day.times.filter((entry) => entry.isAvailable).slice(0, 1).map((entry) => ({
      date: day.value,
      dateLabel: day.dateLabel,
      time: entry.time,
      slotId: entry.slotId,
    }))).slice(0, 5)
    return (
      <div className="agent-context" aria-label="Khung giờ còn trống">
        <div className="agent-context__heading"><span>Khung giờ gần nhất</span><small>Đã ghép đúng xe {car.name}</small></div>
        <div className="agent-context__rail agent-context__rail--slots">
          {quickSlots.map((slot) => (
            <button type="button" key={`${slot.date}-${slot.time}`} onClick={() => onSlot(slot)}>
              <span><Clock size={16} weight="light" /></span>
              <strong>{slot.time}</strong>
              <small>{slot.dateLabel}</small>
            </button>
          ))}
        </div>
      </div>
    )
  }

  return null
}

// Ảnh studio của mẫu xe: dùng chung cho panel mẫu xe, phiếu lịch và bảng đổi xe
// nên mọi bề mặt trong luồng đặt lịch luôn hiển thị dáng xe, không phải ảnh bối cảnh.
function VehicleShot({ car, className = '', eager = false }) {
  return (
    <SmartImage
      className={`vehicle-shot vehicle-shot--${car.studioShot.mode} ${className}`.trim()}
      src={car.studioShot.src}
      alt={`${car.name} — ảnh studio`}
      eager={eager}
    />
  )
}

function VehicleSwitcher({ cars, currentId, onSelect, onClose }) {
  useEffect(() => {
    const handleKey = (event) => { if (event.key === 'Escape') onClose() }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onClose])

  return (
    <div
      className="vehicle-switcher"
      role="dialog"
      aria-modal="true"
      aria-labelledby="vehicle-switcher-title"
      onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}
    >
      <div className="vehicle-switcher__panel">
        <button type="button" className="vehicle-switcher__close" onClick={onClose} aria-label="Đóng bảng chọn xe">
          <X size={17} weight="light" />
        </button>
        <header>
          <p>Đổi mẫu xe lái thử</p>
          <h2 id="vehicle-switcher-title">Bạn muốn cầm lái mẫu nào?</h2>
          <small>ViVi giữ lại địa chỉ và showroom bạn đã chọn; chỉ khung giờ được mở lại để ghép đúng xe mới.</small>
        </header>
        {/* TODO [BACKEND]: Danh sách này cần lọc theo GET /api/v1/test-drive/vehicles?showroomId=
            để chỉ hiện mẫu xe thực sự còn xe lái thử, kèm cờ availability cho từng mẫu. */}
        <div className="vehicle-switcher__body">
          {carGroups.map((group) => (
            <section key={group.id}>
              <div className="vehicle-switcher__group">
                <strong>{group.label}</strong>
                <small>{group.description}</small>
              </div>
              <div className="vehicle-switcher__grid">
                {cars.filter((car) => car.category === group.id).map((car) => {
                  const active = car.id === currentId
                  return (
                    <button
                      type="button"
                      key={car.id}
                      className={active ? 'is-active' : ''}
                      onClick={() => onSelect(car)}
                      aria-pressed={active}
                    >
                      <VehicleShot car={car} className="vehicle-switcher__shot" />
                      <span className="vehicle-switcher__meta">
                        <strong>{car.name}</strong>
                        <small>{car.body} · {car.seats}</small>
                      </span>
                      <span className="vehicle-switcher__state">
                        {active
                          ? <><Check size={13} weight="bold" /> Đang chọn</>
                          : <>Chọn mẫu này <ArrowRight size={13} weight="light" /></>}
                      </span>
                    </button>
                  )
                })}
              </div>
            </section>
          ))}
        </div>
      </div>
    </div>
  )
}

function VehiclePanel({ car, success3d = false }) {
  const hasApproved3dModel = success3d && Boolean(getVehicle3dModel(car.id))
  return (
    <section className={`studio-vehicle ${hasApproved3dModel ? 'has-booking-model' : ''}`} aria-label={`Mẫu xe ${car.name}`}>
      <div className="studio-vehicle__ambient" aria-hidden="true" />
      <div className="studio-vehicle__heading">
        <span>Mẫu xe đang giữ</span>
        <strong>{car.name}</strong>
        <small>{car.body} · {car.seats}</small>
      </div>
      <div className="studio-vehicle__stage" key={car.id}>
        {hasApproved3dModel
          ? <BookingSuccessVehicleModel car={car} className="studio-vehicle__image" />
          : <VehicleShot car={car} className="studio-vehicle__image" eager />}
      </div>
      <div className="studio-vehicle__specs">
        {car.specs.slice(0, 3).map((spec) => (
          <div key={spec.label}><strong>{spec.value}</strong><span>{spec.label}</span></div>
        ))}
      </div>
      <Link to={`/models/${car.id}`}>Xem lại thông tin xe <ArrowRight size={15} weight="light" /></Link>
    </section>
  )
}

function ShowroomMap({ car, showrooms, selectedId, onSelect, onConfirm, userLocation }) {
  const mapContainerRef = useRef(null)
  const mapRef = useRef(null)
  const markersRef = useRef([])
  const userMarkerRef = useRef(null)
  const [leafletLoaded, setLeafletLoaded] = useState(false)

  const selected = showrooms.find((showroom) => showroom.id === selectedId) || null
  const hasLocation = !!userLocation || showrooms.some((s) => s.distance > 0)

  // Load Leaflet CSS and JS dynamically from unpkg CDN
  useEffect(() => {
    if (window.L) {
      setLeafletLoaded(true)
      return
    }

    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
    document.head.appendChild(link)

    const script = document.createElement('script')
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
    script.async = true
    script.onload = () => {
      setLeafletLoaded(true)
    }
    document.body.appendChild(script)
  }, [])

  // Initialize Map
  useEffect(() => {
    if (!leafletLoaded || !mapContainerRef.current) return

    const L = window.L
    const initialCenter = selected
      ? [selected.latitude, selected.longitude]
      : userLocation
      ? [userLocation.latitude, userLocation.longitude]
      : [21.028511, 105.804817] // Hanoi default

    const map = L.map(mapContainerRef.current, {
      zoomControl: false
    }).setView(initialCenter, selected ? 14 : 11)

    L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
      attribution: '&copy; Google Maps'
    }).addTo(map)

    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [leafletLoaded])

  // Update Showroom Markers
  useEffect(() => {
    const map = mapRef.current
    if (!map || !leafletLoaded) return

    const L = window.L

    markersRef.current.forEach(marker => marker.remove())
    markersRef.current = []

    showrooms.forEach((showroom, index) => {
      const isActive = selectedId === showroom.id
      const iconHtml = `<div class="leaflet-showroom-marker ${isActive ? 'is-active' : ''}"><img src="${vinfastLogo}" alt="VinFast" /></div>`

      const customIcon = L.divIcon({
        html: iconHtml,
        className: '',
        iconSize: [32, 32],
        iconAnchor: [16, 16],
        popupAnchor: [0, -16]
      })

      const marker = L.marker([showroom.latitude, showroom.longitude], { icon: customIcon })
        .bindPopup(`<strong>${showroom.name}</strong><br/><small>${showroom.address}</small>`)
        .addTo(map)

      marker.on('click', () => onSelect(showroom.id))
      markersRef.current.push(marker)
    })
  }, [showrooms, selectedId, onSelect, leafletLoaded])

  // Update User Marker
  useEffect(() => {
    const map = mapRef.current
    if (!map || !userLocation || !leafletLoaded) return

    const L = window.L

    if (userMarkerRef.current) {
      userMarkerRef.current.remove()
    }

    const iconHtml = `<div class="leaflet-user-marker"></div>`
    const customIcon = L.divIcon({
      html: iconHtml,
      className: '',
      iconSize: [18, 18],
      iconAnchor: [9, 9]
    })

    const marker = L.marker([userLocation.latitude, userLocation.longitude], { icon: customIcon })
      .addTo(map)

    userMarkerRef.current = marker
  }, [userLocation, leafletLoaded])

  // Smooth Pan
  useEffect(() => {
    const map = mapRef.current
    if (!map || !selected || !leafletLoaded) return

    map.setView([selected.latitude, selected.longitude], 14, {
      animate: true,
      duration: 1.0
    })
  }, [selectedId, leafletLoaded])

  const zoomIn = () => mapRef.current?.zoomIn()
  const zoomOut = () => mapRef.current?.zoomOut()
  const centerUser = () => {
    if (mapRef.current && userLocation) {
      mapRef.current.setView([userLocation.latitude, userLocation.longitude], 14, {
        animate: true
      })
    }
  }

  return (
    <section className="studio-map studio-map--familiar" aria-label="Bản đồ showroom phù hợp">
      <aside className="studio-map__list">
        <div className="studio-map__intro">
          <span>{showrooms.length} showroom có {car.name}</span>
          <small>Ưu tiên có đúng xe, sau đó mới tính khoảng cách</small>
        </div>
        {showrooms.map((showroom, index) => (
          <button
            type="button"
            key={showroom.id}
            className={selectedId === showroom.id ? 'is-active' : ''}
            onClick={() => onSelect(showroom.id)}
          >
            <span>{index + 1}</span>
            <span><strong>{showroom.name}</strong><small>{showroom.address}</small></span>
            {hasLocation && Number.isFinite(showroom.distance) && (
              <em>{formatDistance(showroom.distance)}</em>
            )}
          </button>
        ))}
      </aside>

      <div className="studio-map__canvas">
        <div ref={mapContainerRef} className="studio-map__leaflet-container" />



        <div className="studio-map__controls" aria-label="Điều khiển bản đồ">
          <button type="button" onClick={zoomIn} aria-label="Phóng to"><Plus size={17} weight="regular" /></button>
          <button type="button" onClick={zoomOut} aria-label="Thu nhỏ"><Minus size={17} weight="regular" /></button>
          <button type="button" onClick={centerUser} disabled={!userLocation} aria-label="Vị trí của tôi"><Crosshair size={17} weight="regular" /></button>
        </div>

        {selected && (
          <div className="studio-map__preview">
            <span>
              <strong>{selected.name}</strong>
              <small>
                {selected.address}
                {selected.phone ? ` · SĐT: ${selected.phone}` : ''}
                {hasLocation && Number.isFinite(selected.distance) ? ` · Cách bạn ${formatDistance(selected.distance)}` : ''}
              </small>
            </span>
            <button type="button" onClick={() => onConfirm(selected)} className="studio-map__preview-confirm">
              Xem lịch
            </button>
          </div>
        )}
      </div>
    </section>
  )
}

export function BookingPage() {
  const { bookingStatus, retry } = useBackendStatus()
  // UX state machine (server should return/validate the same nextStage values):
  // idle -> need_car -> need_address -> need_ward -> choose_showroom ->
  // choose_slot -> collect_info -> review -> success. `lookup` is a side flow.
  // The browser may render optimistically, but inventory holds and terminal booking
  // state are always server-authoritative. Full transition table: BACKEND_HANDOFF.md.
  const [searchParams] = useSearchParams()
  const { cars } = useVehicleCatalog()
  const [restoredUi] = useState(readBookingUiState)
  const getCar = (id) => cars.find((car) => car.id === id)
  const featuredChoices = ['vf3', 'vf5', 'vf6', 'vf7'].map(getCar).filter(Boolean)
  const routeCar = getCar(searchParams.get('car'))
  const initialCar = routeCar || null
  const shouldOfferResume = Boolean(
    !initialCar && (
      (restoredUi.stage && restoredUi.stage !== 'idle') ||
      (Array.isArray(restoredUi.messages) && restoredUi.messages.length)
    ),
  )
  const [recipient, setRecipient] = useState(initialCar ? '' : restoredUi.recipient || '')
  const [resumePending, setResumePending] = useState(() => Boolean(
    shouldOfferResume,
  ))
  const [selectedCarId, setSelectedCarId] = useState(initialCar?.id || '')
  const [stage, setStage] = useState(shouldOfferResume ? restoredUi.stage || 'idle' : 'idle')
  const [activeView, setActiveView] = useState(initialCar ? 'car' : 'agent')
  const [messages, setMessages] = useState(shouldOfferResume && Array.isArray(restoredUi.messages) ? restoredUi.messages : [])
  const [draft, setDraft] = useState('')
  const [agentTyping, setAgentTyping] = useState(false)
  const [checkingVehicleName, setCheckingVehicleName] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [address, setAddress] = useState({ province: '', detail: '' })
  const [locationSuggestions, setLocationSuggestions] = useState([])
  const [nearbyShowrooms, setNearbyShowrooms] = useState(Array.isArray(restoredUi.nearbyShowrooms) ? restoredUi.nearbyShowrooms : [])
  const [showroomId, setShowroomId] = useState(restoredUi.showroomId || '')
  const [pendingSlot, setPendingSlot] = useState(null)
  const [selectedSlot, setSelectedSlot] = useState(null)
  const [confirmSlotOpen, setConfirmSlotOpen] = useState(false)
  const [switcherOpen, setSwitcherOpen] = useState(false)
  const [workspaceHidden, setWorkspaceHidden] = useState(false)
  const [person, setPerson] = useState({ bookingName: '', driverName: '', phone: '', email: '', hasLicense: false, marketingConsent: true })
  const [formErrors, setFormErrors] = useState({})
  const [bookingCode, setBookingCode] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [successCinematic, setSuccessCinematic] = useState(false)
  const [accessFlow, setAccessFlow] = useState(null)
  const [accessValue, setAccessValue] = useState({ phone: '', otpCode: '' })
  const [accessError, setAccessError] = useState('')
  const [accessBusy, setAccessBusy] = useState(false)
  const [accessSecondsLeft, setAccessSecondsLeft] = useState(0)
  const [resendSecondsLeft, setResendSecondsLeft] = useState(0)
  const [accessProfile, setAccessProfile] = useState(null)
  const [accessibleBookings, setAccessibleBookings] = useState([])
  const [expandedBookingId, setExpandedBookingId] = useState('')
  const [rescheduleState, setRescheduleState] = useState(null)
  const [rescheduleSecondsLeft, setRescheduleSecondsLeft] = useState(0)
  const [slots, setSlots] = useState(Array.isArray(restoredUi.slots) ? restoredUi.slots : [])
  const [bookingId, setBookingId] = useState('')
  const [bookingVersion, setBookingVersion] = useState(0)
  const [holdExpiresAt, setHoldExpiresAt] = useState(null)
  const [timeLeft, setTimeLeft] = useState('')
  const [backendError, setBackendError] = useState('')
  const [userLocation, setUserLocation] = useState(null)
  const messagesRef = useRef(null)
  const timersRef = useRef([])
  const holdActionIdsRef = useRef(new Map())
  const confirmActionIdsRef = useRef(new Map())
  const holdExpiredRef = useRef(false)
  const otpChallengeIdRef = useRef('')
  const otpCodeRef = useRef('')
  const sendingRef = useRef(false)

  const selectedCar = getCar(selectedCarId)
  // ĐÃ XONG: showroom và khung giờ lấy thật từ backend qua searchBookingOptions().
  // Mỗi slot đã mang id thật của backend; cặp ngày/giờ trong UI chỉ để hiển thị.
  const selectedShowroom = nearbyShowrooms.find((showroom) => showroom.id === showroomId)
  const composerDisabled = isSending || agentTyping

  const completeBookingSuccess = useCallback(() => {
    setSuccessCinematic(false)
    setStage('success')
    setMessages((current) => [...current, {
      id: `${Date.now()}-${current.length}`,
      role: 'assistant',
      text: 'Đặt lịch thành công. Tôi đã giữ lại toàn bộ thông tin bên cạnh. Sau này, bạn chỉ cần nhập họ tên và số điện thoại để tra cứu, bổ sung hoặc huỷ lịch.',
    }])
  }, [])

  useEffect(() => {
    const config = getVehicle3dModel(selectedCarId)
    if (!config) return undefined

    // Người dùng thường mất vài phút để chọn showroom và điền form. Tận dụng quãng
    // đó để browser cache GLB + runtime, tránh màn chờ ngay sau nút xác nhận cuối.
    preloadVehicle3dRuntime().catch(() => {})
    const link = document.createElement('link')
    link.rel = 'prefetch'
    link.as = 'fetch'
    link.type = 'model/gltf-binary'
    link.href = config.src
    link.crossOrigin = 'anonymous'
    document.head.appendChild(link)
    return () => link.remove()
  }, [selectedCarId])

  useEffect(() => {
    const safeMessages = messages
      .filter((message) => !isSensitiveChatText(message.text || ''))
      .slice(-30)
    window.sessionStorage.setItem(BOOKING_UI_STATE_KEY, JSON.stringify({
      recipient,
      selectedCarId,
      stage,
      activeView,
      showroomId,
      nearbyShowrooms,
      slots,
      messages: safeMessages,
    }))
  }, [recipient, selectedCarId, stage, activeView, showroomId, nearbyShowrooms, slots, messages])

  useEffect(() => {
    if (selectedCarId || !cars.length) return
    const requestedCar = getCar(searchParams.get('car'))
    if (!requestedCar) return
    setSelectedCarId(requestedCar.id)
    setActiveView('car')
    setWorkspaceHidden(false)
  }, [cars, searchParams, selectedCarId])

  const mapShowrooms = (items, vehicleId = selectedCarId) => items.map((item, index) => ({
    ...item,
    distance: item.distance_km,
    x: 20 + ((index * 23) % 65),
    y: 25 + ((index * 19) % 55),
    models: [vehicleId],
  }))

  const groupSlots = (items) => Object.values(items.reduce((groups, item) => {
    const start = new Date(item.start_at)
    const value = item.start_at.slice(0, 10)
    const time = start.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', hour12: false })
    if (!groups[value]) groups[value] = {
      value,
      dateLabel: new Intl.DateTimeFormat('vi-VN', { weekday: 'short', day: '2-digit', month: '2-digit' }).format(start),
      times: [],
    }
    groups[value].times.push({ time, slotId: item.id, isAvailable: item.status === 'available', unavailableLabel: item.status === 'held' ? 'Đang được giữ' : 'Đã có lịch' })
    return groups
  }, {}))

  const resolveAgentCar = (vehicle) => {
    if (!vehicle) return null
    const normalize = (value) => String(value || '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/[^a-z0-9]/g, '')
    const source = typeof vehicle === 'string' ? { name: vehicle } : vehicle
    const candidates = [
      normalize(source.id),
      normalize(source.code),
      normalize(source.name),
      normalize(source.model),
      normalize(source.vehicle_model),
    ].filter(Boolean)
    return cars.find((car) => candidates.includes(normalize(car.id)) || candidates.includes(normalize(car.name))) || null
  }

  const requestUserLocation = () => {
    if (!navigator.geolocation) {
      setBackendError("Trình duyệt của bạn không hỗ trợ định vị GPS.")
      return
    }

    setBackendError('')
    addMessage('user', 'Định vị vị trí hiện tại của tôi.')
    setAgentTyping(true)

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords
        setUserLocation({ latitude, longitude })
        
        try {
          const result = await searchBookingOptions({
            vehicleModel: selectedCar.name,
            latitude: latitude,
            longitude: longitude,
          })
          const showrooms = mapShowrooms(result.showrooms || [], selectedCar.id)
          setAddress({ province: '', detail: 'Vị trí hiện tại' })
          setLocationSuggestions([])
          setNearbyShowrooms(showrooms)
          setAgentTyping(false)
          if (showrooms.length) {
            setStage('choose_showroom')
            setActiveView('map')
            addMessage('assistant', `Tôi đã định vị vị trí và tìm thấy ${showrooms.length} showroom gần bạn nhất có xe ${selectedCar.name}. Mời bạn chọn showroom hiển thị trên bản đồ để tiếp tục đặt lịch.`)
          } else {
            setStage('need_address')
            addMessage('assistant', `Rất tiếc, tôi chưa tìm thấy showroom nào gần vị trí của bạn có sẵn xe ${selectedCar.name}. Bạn hãy thử nhập một địa chỉ cụ thể khác ở khung chat bên dưới nhé.`)
          }
        } catch (error) {
          setAgentTyping(false)
          addMessage('assistant', `Có lỗi xảy ra khi truy vấn dữ liệu showroom: ${error.message}`)
        }
      },
      (error) => {
        setAgentTyping(false)
        console.error("Lỗi lấy vị trí: ", error)
        addMessage('assistant', 'Tôi không nhận được phản hồi định vị. Hãy nhắn cho tôi quận/huyện hoặc tỉnh/thành phố của bạn (ví dụ: "Quận 1, TP HCM") để tôi tìm showroom nhé!')
      }
    )
  }

  const primeLocationSuggestions = async (car) => {
    try {
      const result = await searchBookingOptions({ vehicleModel: car.name })
      setLocationSuggestions(mapShowrooms(result.showrooms || [], car.id))
    } catch (error) {
      setBackendError(error.message)
      setLocationSuggestions([])
    }
  }

  const applyAgentToolResult = (result) => {
    if (!result || !result.action_data) return
    setWorkspaceHidden(false)

    if (result.tool_name === 'search_test_drive_options') {
      const data = result.action_data
      const toolInput = result.tool_input || {}
      const agentCar = resolveAgentCar(data.resolved_vehicle)
      const vehicleId = agentCar?.id || selectedCarId

      if (agentCar) {
        setSelectedCarId(agentCar.id)
      }

      if (data.search_stage === 'showroom_selection') {
        const mapped = mapShowrooms(data.showrooms || [], vehicleId)
        const queriedAddress = String(toolInput.address || '').trim()
        setPendingSlot(null)
        setSelectedSlot(null)
        setConfirmSlotOpen(false)
        setShowroomId('')

        if (queriedAddress) {
          setAddress({ province: '', detail: queriedAddress })
          setUserLocation(null)
          setLocationSuggestions([])
          setNearbyShowrooms(mapped)
          setStage(mapped.length ? 'choose_showroom' : 'need_address')
          setActiveView(mapped.length ? 'map' : 'car')
        } else {
          setAddress({ province: '', detail: '' })
          setNearbyShowrooms([])
          setLocationSuggestions(mapped.slice(0, 5))
          setStage('need_address')
          setActiveView('car')
        }
        return
      }

      if (data.search_stage === 'slot_selection' && data.selected_showroom) {
        const [showroom] = mapShowrooms([data.selected_showroom], vehicleId)
        setLocationSuggestions([])
        setNearbyShowrooms((current) => current.some((item) => item.id === showroom.id) ? current : [...current, showroom])
        setShowroomId(showroom.id)
        setSlots(groupSlots(data.slots || []))
        setStage('choose_slot')
        setActiveView('schedule')
      }
      return
    }

    if (result.tool_name === 'hold_test_drive_slot') {
      const data = result.action_data
      const toolInput = result.tool_input || {}
      setBookingId(data.booking_id)
      setBookingVersion(data.version ?? 1)
      setHoldExpiresAt(data.hold_expires_at ? new Date(data.hold_expires_at).getTime() : Date.now() + 120000)

      if (data.showroom) {
        const [mappedShowroom] = mapShowrooms([data.showroom], selectedCarId)
        setNearbyShowrooms((current) => current.some((item) => item.id === mappedShowroom.id) ? current : [...current, mappedShowroom])
        setShowroomId(mappedShowroom.id)
      }

      let foundSlot = null
      for (const group of slots) {
        const match = group.times.find(item => item.slotId === toolInput.slot_id)
        if (match) {
          foundSlot = match
          break
        }
      }

      const targetSlot = foundSlot || {
        slotId: toolInput.slot_id,
        time: '21:00 - 22:00',
        dateLabel: 'Ngày đã chọn',
      }

      setPendingSlot(targetSlot)
      setSelectedSlot(targetSlot)
      setConfirmSlotOpen(true)
      setActiveView('schedule')
      return
    }

    if (result.tool_name === 'update_booking_draft' || result.tool_name === 'get_booking_draft') {
      const data = result.action_data
      setBookingId(data.id)
      setBookingVersion(data.version ?? 1)
      if (data.hold_expires_at) {
        setHoldExpiresAt(new Date(data.hold_expires_at).getTime())
      }

      const newRecipient = data.recipient_type || 'self'
      setRecipient(newRecipient)

      setPerson({
        bookingName: data.booker?.name || '',
        driverName: data.driver?.name || '',
        phone: data.booker?.phone || '',
        email: data.booker?.email || '',
        hasLicense: !!data.license_declaration?.has_driving_license,
      })

      if (stage === 'choose_slot' || stage === 'choose_showroom' || stage === 'need_address') {
        if (data.showroom) {
          const [mappedShowroom] = mapShowrooms([data.showroom], selectedCarId)
          setNearbyShowrooms((current) => current.some((item) => item.id === mappedShowroom.id) ? current : [...current, mappedShowroom])
          setShowroomId(mappedShowroom.id)
        }

        let foundSlot = null
        if (data.slot_id) {
          for (const group of slots) {
            const match = group.times.find(item => item.slotId === data.slot_id)
            if (match) {
              foundSlot = match
              break
            }
          }
        }

        const targetSlot = foundSlot || {
          slotId: data.slot_id || 'temp-id',
          time: data.slot_time || '21:00 - 22:00',
          dateLabel: data.slot_date || 'Ngày đã chọn',
        }

        setPendingSlot(targetSlot)
        setSelectedSlot(targetSlot)
        setConfirmSlotOpen(true)
        setActiveView('schedule')
        setStage('choose_slot')
        return
      }

      const isComplete = data.booker?.name && data.booker?.phone && data.license_declaration?.has_driving_license
      if (isComplete) {
        setStage('review')
        setActiveView('ticket')
      } else {
        setStage('collect_info')
        setActiveView('schedule')
      }
      return
    }

    if (result.tool_name === 'confirm_test_drive_booking') {
      const data = result.action_data
      setBookingCode(data.booking_code)
      setStage('success')
    }
  }

  const loadShowrooms = async (car, detail, province = '') => {
    setBackendError('')
    setAgentTyping(true)
    try {
      const result = await searchBookingOptions({ vehicleModel: car.name, address: detail })
      const showrooms = mapShowrooms(result.showrooms || [], car.id)
      setAddress({ province, detail })
      setLocationSuggestions([])
      setNearbyShowrooms(showrooms)
      setAgentTyping(false)
      if (showrooms.length) {
        setStage('choose_showroom')
        setActiveView('map')
        reply(`Đã tìm thấy ${showrooms.length} showroom đang có ${car.name} gần “${detail}”. Hãy chọn một showroom để xem lịch trống thực tế.`)
      } else {
        setStage('need_address')
        setActiveView('car')
        reply(`Tôi chưa tìm thấy showroom có ${car.name} gần “${detail}”. Bạn hãy nhập địa chỉ khác, kèm phường/xã và tỉnh/thành phố.`)
      }
    } catch (error) {
      setAgentTyping(false)
      setStage('need_address')
      setActiveView('car')
      reply(`Không tìm được showroom từ địa chỉ này: ${error.message}`)
    }
  }

  useEffect(() => () => timersRef.current.forEach((timer) => window.clearTimeout(timer)), [])
  useEffect(() => {
    messagesRef.current?.scrollTo({ top: messagesRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, stage, agentTyping])

  useEffect(() => {
    if (!holdExpiresAt || (stage !== 'collect_info' && stage !== 'review')) {
      setTimeLeft('')
      return
    }

    const updateTimer = () => {
      const diff = holdExpiresAt - Date.now()
      if (diff <= 0) {
        setTimeLeft('Đã hết hạn giữ')
        if (!holdExpiredRef.current) {
          holdExpiredRef.current = true
          setConfirmSlotOpen(false)
          setPendingSlot(null)
          setSelectedSlot(null)
          setBookingId('')
          setBookingVersion(0)
          setSubmitting(false)
          setStage('choose_slot')
          setActiveView('schedule')
          addMessage('assistant', 'Khung giờ giữ tạm đã hết hạn. Bạn vui lòng chọn lại một thời gian khác để tiếp tục đặt lịch.')
        }
        return
      }
      const min = Math.floor(diff / 60000)
      const sec = Math.floor((diff % 60000) / 1000)
      setTimeLeft(`${min.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`)
    }

    updateTimer()
    const interval = setInterval(updateTimer, 1000)
    return () => clearInterval(interval)
  }, [holdExpiresAt, stage])

  useEffect(() => {
    holdExpiredRef.current = false
  }, [holdExpiresAt])

  const addMessage = (role, text) => {
    // TODO [BACKEND/AGENT]: Use server message ids and timestamps. Store structured
    // cards/actions separately from display text so UI choices stay deterministic.
    setMessages((current) => [...current, { id: `${Date.now()}-${current.length}`, role, text }])
  }

  const reply = (text, delay = 420) => {
    // TODO [BACKEND/AGENT]: Replace this cosmetic delay with streamed message state
    // from a future streaming form of POST /api/v1/chat (SSE or fetch stream). Cancel the
    // previous request on stage/vehicle changes and expose retry on failure.
    setAgentTyping(true)
    const timer = window.setTimeout(() => {
      setAgentTyping(false)
      addMessage('assistant', text)
    }, delay)
    timersRef.current.push(timer)
  }

  const beginConversation = (choice) => {
    // TODO [BACKEND/SESSION]: Create/resume an anonymous booking draft here and
    // persist recipientType + selectedVehicleId. Return draftId and expiresAt.
    setRecipient(choice)
    const car = selectedCar
    addMessage(
      'assistant',
      'Xin chào, tôi là ViVi — trợ lý đặt lịch lái thử VinFast. Tôi có thể tạo lịch mới hoặc hỗ trợ tra cứu, bổ sung và huỷ lịch đã đặt.',
    )
    if (car) {
      setStage('need_address')
      setActiveView('car')
      primeLocationSuggestions(car)
      reply(`Bạn đang xem ${car.name}. Hãy nhập địa chỉ theo phường/xã và tỉnh/thành phố để tôi tìm showroom có xe lái thử gần bạn.`, 520)
    } else {
      setStage('need_car')
      setActiveView('agent')
      reply('Trước tiên, bạn muốn lái thử mẫu xe nào? Bạn có thể chọn một mẫu ngay phía trên ô nhập hoặc nhắn tên xe cho tôi.', 520)
    }
  }

  const chooseCar = (car, fromPrompt = false) => {
    setSelectedCarId(car.id)
    setWorkspaceHidden(false)
    if (!fromPrompt) addMessage('user', `Tôi muốn lái thử ${car.name}.`)
    setNearbyShowrooms([])
    setLocationSuggestions([])
    setShowroomId('')
    setStage('need_address')
    setActiveView('car')
    primeLocationSuggestions(car)
    reply(`Đã chọn ${car.name}. Bây giờ bạn hãy nhập địa chỉ theo phường/xã và tỉnh/thành phố để tôi tìm showroom gần nhất.`)
  }

  // Đổi mẫu xe sẽ quay lại bước địa chỉ để Agent kiểm tra tồn xe/showroom lại từ đầu.
  const switchCar = (car) => {
    setSwitcherOpen(false)
    if (!car || car.id === selectedCarId) return

    setSelectedCarId(car.id)
    setPendingSlot(null)
    setSelectedSlot(null)
    setConfirmSlotOpen(false)
    addMessage('user', `Tôi muốn đổi sang ${car.name}.`)

    setAddress({ province: '', detail: '' })
    setLocationSuggestions([])
    setNearbyShowrooms([])
    setShowroomId('')
    setStage('need_address')
    setActiveView('car')
    primeLocationSuggestions(car)
    reply(`Đã đổi sang ${car.name}. Bạn cho tôi lại địa chỉ theo phường hoặc xã và tỉnh/thành phố để tìm showroom có sẵn mẫu này.`)
  }

  // Bảng chọn xe dùng chung cho lần chọn đầu tiên và cho việc đổi xe giữa chừng.
  const pickCarFromSwitcher = (car) => {
    setSwitcherOpen(false)
    if (!selectedCarId) chooseCar(car)
    else switchCar(car)
  }

  const resolveSuggestedArea = (showroom) => {
    addMessage('user', `Tìm quanh ${showroom.address}.`)
    loadShowrooms(selectedCar, showroom.address, showroom.province)
  }

  const chooseShowroom = async (showroom, fromPrompt = false) => {
    // ĐÃ XONG một phần: khung giờ đã là dữ liệu thật theo showroom + mẫu xe.
    // TODO [BACKEND/DRAFT — P0]: chưa lưu showroomId lên draft phía server nên đổi máy
    // là mất tiến trình. Chi tiết ở mục 1.3 trong BACKEND_HANDOFF.md.
    if (!fromPrompt) addMessage('user', `Tôi chọn ${showroom.name}.`)
    setWorkspaceHidden(false)
    setShowroomId(showroom.id)
    setBackendError('')
    setAgentTyping(true)
    try {
      const result = await searchBookingOptions({ vehicleModel: selectedCar.name, showroomId: showroom.id })
      const grouped = groupSlots(result.slots || [])
      setSlots(grouped)
      setStage('choose_slot')
      setActiveView('schedule')
      setAgentTyping(false)
      reply(`${showroom.name} đã được chọn. ViVi đã tìm thấy ${result.slots?.length || 0} khung giờ trống cho bạn.`)
    } catch (error) {
      setAgentTyping(false)
      reply(`Không tải được lịch trống: ${error.message}`)
    }
  }

  const chooseSlot = (slot) => {
    setPendingSlot(slot)
    setConfirmSlotOpen(true)
  }

  const confirmSlot = async () => {
    setBackendError('')
    setAgentTyping(true)
    try {
      if (bookingId && selectedSlot && selectedSlot.slotId === pendingSlot.slotId) {
        setConfirmSlotOpen(false)
        setStage('collect_info')
        setAgentTyping(false)
        return
      }
      const actionKey = pendingSlot.slotId
      const uiActionId = holdActionIdsRef.current.get(actionKey) || actionId('hold')
      holdActionIdsRef.current.set(actionKey, uiActionId)
      const held = await holdBookingSlot(pendingSlot.slotId, uiActionId)
      holdActionIdsRef.current.delete(actionKey)
      setBookingId(held.booking_id)
      setBookingVersion(held.version ?? 1)
      setHoldExpiresAt(held.hold_expires_at ? new Date(held.hold_expires_at).getTime() : Date.now() + 120000)
      setSelectedSlot(pendingSlot)
      setConfirmSlotOpen(false)
      addMessage('user', `Tôi xác nhận ${pendingSlot.time}, ${pendingSlot.dateLabel}.`)
      setStage('collect_info')
      setAgentTyping(false)
      reply('ViVi đã giữ tạm khung giờ này cho bạn trong 2 phút. Bạn vui lòng điền thông tin để tiếp tục nhé.')
    } catch (error) {
      setAgentTyping(false)
      setConfirmSlotOpen(false)
      if (error.code === 'SLOT_NO_LONGER_AVAILABLE') {
        setPendingSlot(null)
        setSelectedSlot(null)
        if (selectedCar && selectedShowroom) {
          try {
            const refreshed = await searchBookingOptions({ vehicleModel: selectedCar.name, showroomId: selectedShowroom.id })
            setSlots(groupSlots(refreshed.slots || []))
          } catch {
            setSlots([])
          }
        }
      }
      reply(`Không thể giữ khung giờ: ${error.message}`)
    }
  }

  const handlePrompt = async (event) => {
    event.preventDefault()
    if (sendingRef.current) return
    const value = draft.trim()
    if (!value) return
    if (value.length > CHAT_MESSAGE_MAX_LENGTH) {
      setBackendError(`Tin nhắn không được vượt quá ${CHAT_MESSAGE_MAX_LENGTH.toLocaleString('vi-VN')} ký tự.`)
      return
    }
    sendingRef.current = true
    setIsSending(true)
    setDraft('')
    addMessage('user', value)
    setBackendError('')

    // Vehicle text is only a hint for the pending status. The panel changes after
    // the Agent tool confirms an active model in applyAgentToolResult().
    const mentionedCar = resolveAgentCar(value)
    setCheckingVehicleName(mentionedCar?.name || '')

    setAgentTyping(true)
    try {
      const result = await sendBookingMessage(value, {
        stage,
        recipient,
        selectedVehicle: selectedCar ? { id: selectedCar.id, name: selectedCar.name } : null,
        selectedShowroom: selectedShowroom ? { id: selectedShowroom.id, name: selectedShowroom.name } : null,
        selectedSlot,
        nearbyShowrooms: nearbyShowrooms.map((showroom) => ({
          id: showroom.id,
          name: showroom.name,
          address: showroom.address,
          distance: showroom.distance,
        })),
        userLocation,
        bookingId: bookingId || null,
        channel: 'booking',
      })
      applyAgentToolResult(result)
      addMessage('assistant', result.response)
    } catch (error) {
      addMessage('assistant', `Không thể kết nối ViVi: ${error.message}`)
    } finally {
      setAgentTyping(false)
      setCheckingVehicleName('')
      sendingRef.current = false
      setIsSending(false)
    }
  }

  const startLookup = () => {
    // ĐÃ XONG: tra cứu chạy thật qua requestBookingAccess + verifyBookingAccess
    // (OTP gửi bằng Zalo). Chỉ sau khi xác thực mới mở được sửa/huỷ/đổi lịch.
    // TODO [BACKEND/ENDPOINT — P0]: các action này vẫn đi qua /api/v1/demo/action;
    // cần endpoint mang tên thật cho nghiệp vụ production.
    addMessage('user', 'Tôi muốn tra cứu lịch đã đặt.')
    setStage('lookup')
    setAccessError('')
    otpChallengeIdRef.current = ''
    // A lookup/edit session also needs reschedule permission for the calendar
    // icon. The backend grants update_details as part of this purpose.
    setAccessFlow({ phase: 'request', purpose: 'reschedule', challengeId: '', expiresAt: 0 })
    reply('Để bảo vệ lịch của bạn, hãy nhập mã lịch và số điện thoại. Tôi sẽ gửi OTP qua Zalo đã liên kết.')
  }

  const changeAccessValue = (field, value) => {
    if (field === 'otpCode') otpCodeRef.current = value
    setAccessValue((current) => ({ ...current, [field]: value }))
  }

  const requestAccessOtp = async (event) => {
    event?.preventDefault()
    setAccessBusy(true); setAccessError('')
    try {
      const result = await requestBookingAccess({ phone: accessValue.phone.trim(), purpose: accessFlow?.purpose || 'update_details' })
      if (!result?.challenge_id || !result?.expires_at) {
        throw new Error('Không thể khởi tạo phiên xác thực OTP. Vui lòng gửi lại mã.')
      }
      const expiresAt = new Date(result.expires_at).getTime()
      if (Number.isNaN(expiresAt)) {
        throw new Error('Thời hạn OTP không hợp lệ. Vui lòng gửi lại mã.')
      }
      otpChallengeIdRef.current = result.challenge_id
      setAccessFlow((current) => ({ phase: 'verify', purpose: current?.purpose || 'update_details', challengeId: result.challenge_id, expiresAt }))
      otpCodeRef.current = ''
      setAccessValue((current) => ({ ...current, otpCode: '' }))
      setAccessSecondsLeft(Math.max(0, Math.ceil((expiresAt - Date.now()) / 1000)))
      setResendSecondsLeft(result.retry_after_seconds || 60)
      addMessage('assistant', 'Tôi đã gửi mã OTP qua Zalo. Bạn vui lòng nhập mã để tiếp tục.')
    } catch (error) {
      if (error.code === 'OTP_RATE_LIMITED') {
        const seconds = Number(error.message.match(/\d+/)?.[0] || 0)
        setResendSecondsLeft(seconds)
      }
      setAccessError('')
      addMessage('assistant', error.message)
    } finally { setAccessBusy(false) }
  }

  const verifyAccessOtp = async (otpOverride = '') => {
    const challengeId = otpChallengeIdRef.current || accessFlow?.challengeId
    if (!challengeId) {
      setAccessError('')
      addMessage('assistant', 'Phiên OTP chưa sẵn sàng hoặc đã hết hạn. Vui lòng gửi lại mã.')
      return
    }
    setAccessBusy(true); setAccessError('')
    try {
      const otpCode = typeof otpOverride === 'string' && otpOverride ? otpOverride : otpCodeRef.current
      const verified = await verifyBookingAccess({ challengeId, otpCode })
      const booking = await getVerifiedBooking({ accessToken: verified.access_session_token, bookingId: verified.booking_id })
      const bookings = await listVerifiedBookings({ accessToken: verified.access_session_token })
      setAccessibleBookings(bookings.data || bookings)
      setAccessSecondsLeft(0)
      setResendSecondsLeft(0)
      setAccessProfile({
        accessToken: verified.access_session_token,
        bookingId: booking.id,
        bookingCode: booking.booking_code || '',
        bookerName: booking.booker?.full_name || '',
        driverName: booking.driver?.full_name || '',
        phone: booking.driver?.phone || booking.booker?.phone || '',
        email: booking.driver?.email || booking.booker?.email || '',
        vehicleName: booking.vehicle?.name || '',
        vehicleModelId: booking.vehicle?.id || '',
        showroomName: booking.showroom?.name || '',
        showroomId: booking.showroom?.id || '',
        showroomAddress: booking.showroom?.address || '',
        advisorName: booking.advisor?.full_name || 'Chưa phân công',
        advisorPhone: booking.advisor?.phone || '',
        slotTime: booking.slot_time || '',
        slotDate: booking.slot_date || '',
      })
      setExpandedBookingId(booking.id)
      setWorkspaceHidden(false)
      setActiveView('bookings')
      const isCancellation = accessFlow?.purpose === 'cancel'
      setAccessFlow({ phase: isCancellation ? 'confirm_cancel' : 'edit', purpose: accessFlow?.purpose, challengeId: '', expiresAt: 0 })
      otpChallengeIdRef.current = ''
      otpCodeRef.current = ''
      addMessage('assistant', isCancellation ? 'Xác thực thành công. Vui lòng kiểm tra phiếu bên dưới và xác nhận nếu bạn muốn hủy lịch.' : 'Xác thực thành công. Bạn có thể cập nhật thông tin lịch đã đặt bên dưới.')
    } catch (error) { setAccessError(''); addMessage('assistant', error.message) } finally { setAccessBusy(false) }
  }

  const cancelAccessOtp = () => {
    setAccessFlow(null); setAccessError(''); setAccessSecondsLeft(0); setResendSecondsLeft(0)
    otpChallengeIdRef.current = ''
    otpCodeRef.current = ''
    addMessage('assistant', 'Tôi đã dừng bước xác thực. Khi cần xem hoặc chỉnh sửa lịch, bạn có thể yêu cầu lại bất cứ lúc nào.')
  }
  const resumeConversation = () => {
    // Nháp tạo trước khi lưu recipient không đủ dữ liệu để hiện lại modal;
    // tiếp tục thẳng với lựa chọn mặc định thay vì chặn người dùng thêm lần nữa.
    if (!recipient) setRecipient('self')
    if (restoredUi.selectedCarId) setSelectedCarId(restoredUi.selectedCarId)
    if (restoredUi.activeView) setActiveView(restoredUi.activeView)
    setResumePending(false)
  }
  const restartConversation = () => {
    window.sessionStorage.removeItem(BOOKING_UI_STATE_KEY)
    window.location.reload()
  }

  const selectAccessibleBooking = async (summary) => {
    if (!accessProfile?.accessToken) return
    setAccessBusy(true); setAccessError('')
    try {
      const booking = await getVerifiedBooking({ accessToken: accessProfile.accessToken, bookingId: summary.id })
      const selectedProfile = { ...accessProfile, bookingId: booking.id, bookingCode: booking.booking_code || '', bookerName: booking.booker?.full_name || '', driverName: booking.driver?.full_name || '', phone: booking.driver?.phone || booking.booker?.phone || '', email: booking.driver?.email || booking.booker?.email || '', vehicleName: booking.vehicle?.name || '', vehicleModelId: booking.vehicle?.id || '', showroomName: booking.showroom?.name || '', showroomId: booking.showroom?.id || '', showroomAddress: booking.showroom?.address || '', advisorName: booking.advisor?.full_name || 'Chưa phân công', advisorPhone: booking.advisor?.phone || '', slotTime: booking.slot_time || '', slotDate: booking.slot_date || '' }
      setAccessProfile(selectedProfile)
      return selectedProfile
    } catch (error) { setAccessError(error.message) } finally { setAccessBusy(false) }
  }

  const changeAccessProfile = (field, value) => setAccessProfile((current) => ({ ...current, [field]: value }))
  const saveAccessProfile = async (event) => {
    event.preventDefault()
    if (!accessProfile) return
    if (rescheduleState?.step === 'pending') {
      setRescheduleState((current) => ({ ...current, step: 'confirm' }))
      return
    }
    setAccessBusy(true); setAccessError('')
    try {
      await updateVerifiedBooking({
        bookingId: accessProfile.bookingId,
        accessToken: accessProfile.accessToken,
        bookerPatch: { full_name: accessProfile.bookerName, phone: accessProfile.phone, email: accessProfile.email },
        // Chỉ sửa thông tin người đặt trên panel khách hàng; không đổi người lái thử của lịch hiện có.
        driverPatch: null,
        driverSameAsBooker: false,
      })
      setAccessFlow(null)
      addMessage('assistant', 'ViVi đã cập nhật thông tin đặt lịch của bạn.')
    } catch (error) { setAccessError(error.message) } finally { setAccessBusy(false) }
  }

  const confirmCancellation = async () => {
    if (!accessProfile) return
    setAccessBusy(true); setAccessError('')
    try {
      await cancelVerifiedBooking({ bookingId: accessProfile.bookingId, accessToken: accessProfile.accessToken })
      setAccessFlow(null); setAccessProfile(null)
      addMessage('assistant', `ViVi đã hủy lịch ${accessProfile.bookingCode}. Khung giờ đã được mở lại.`)
    } catch (error) { setAccessError(error.message) } finally { setAccessBusy(false) }
  }

  const loadRescheduleSlots = async (car, showroom) => {
    setAccessBusy(true); setAccessError('')
    try {
      const result = await searchBookingOptions({ vehicleModel: car.name, showroomId: showroom.id })
      const slots = result.slots || []
      if (slots.some((slot) => slot.status === 'available')) setRescheduleState({ step: 'schedule', car, showroom, slots })
      else {
        const alternatives = await searchBookingOptions({ vehicleModel: car.name })
        setRescheduleState({ step: 'showroom', car, showrooms: alternatives.showrooms || [] })
      }
    } catch (error) { setAccessError(error.message) } finally { setAccessBusy(false) }
  }
  const beginTimeReschedule = (targetProfile = accessProfile) => {
    const car = cars.find((item) => item.id === targetProfile?.vehicleModelId)
      || cars.find((item) => normalizeVehicleName(item.name) === normalizeVehicleName(targetProfile?.vehicleName))
    if (car && targetProfile?.showroomId) {
      setSelectedCarId(car.id)
      setStage('lookup')
      setWorkspaceHidden(false)
      setActiveView('schedule')
      loadRescheduleSlots(car, { id: targetProfile.showroomId, name: targetProfile.showroomName })
    } else setAccessError('Không xác định được mẫu xe hoặc showroom của lịch này.')
  }
  const beginAccessibleReschedule = async (summary) => {
    const targetProfile = summary.id === accessProfile?.bookingId ? accessProfile : await selectAccessibleBooking(summary)
    if (targetProfile) beginTimeReschedule(targetProfile)
  }
  const holdReschedule = async (slot) => {
    setAccessBusy(true); setAccessError('')
    try {
      const held = await holdVerifiedReschedule({ bookingId: accessProfile.bookingId, slotId: slot.id, accessToken: accessProfile.accessToken })
      const startsAt = new Date(slot.start_at)
      setAccessProfile((current) => ({ ...current, slotTime: startsAt.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', hour12: false }), slotDate: new Intl.DateTimeFormat('vi-VN', { weekday: 'long', day: '2-digit', month: '2-digit' }).format(startsAt) }))
      setRescheduleState((current) => ({ ...current, step: 'pending', slot, newBookingId: held.booking_id }))
      setRescheduleSecondsLeft(Math.max(0, Math.ceil((new Date(held.hold_expires_at).getTime() - Date.now()) / 1000)))
      setExpandedBookingId(accessProfile.bookingId)
      setActiveView('bookings')
      addMessage('assistant', 'ViVi đã giữ tạm khung giờ mới và cập nhật trên phiếu. Bạn bấm “Cập nhật thông tin” để kiểm tra, xác nhận toàn bộ lịch.')
    } catch (error) { setAccessError(error.message) } finally { setAccessBusy(false) }
  }
  const confirmReschedule = async () => {
    setAccessBusy(true); setAccessError('')
    try {
      await updateVerifiedBooking({
        bookingId: accessProfile.bookingId,
        accessToken: accessProfile.accessToken,
        bookerPatch: { full_name: accessProfile.bookerName, phone: accessProfile.phone, email: accessProfile.email },
        driverPatch: accessProfile.driverName.trim() === accessProfile.bookerName.trim() ? null : { full_name: accessProfile.driverName, phone: accessProfile.phone, email: accessProfile.email },
        driverSameAsBooker: accessProfile.driverName.trim() === accessProfile.bookerName.trim(),
      })
      await confirmVerifiedReschedule({ bookingId: accessProfile.bookingId, newBookingId: rescheduleState.newBookingId, accessToken: accessProfile.accessToken })
      const startsAt = new Date(rescheduleState.slot.start_at)
      setAccessProfile((current) => ({ ...current, bookingId: rescheduleState.newBookingId, slotTime: startsAt.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', hour12: false }), slotDate: new Intl.DateTimeFormat('vi-VN', { weekday: 'long', day: '2-digit', month: '2-digit' }).format(startsAt) }))
      setRescheduleState(null); setRescheduleSecondsLeft(0); setAccessFlow(null); setAccessProfile(null)
      addMessage('assistant', `ViVi đã đổi lịch thành công. Mã lịch ${accessProfile.bookingCode} được giữ nguyên. Tôi đã gửi thông tin lịch mới qua Zalo.`)
    } catch (error) { setAccessError(error.message) } finally { setAccessBusy(false) }
  }

  useEffect(() => {
    if (accessFlow?.phase !== 'verify' && !(accessFlow?.phase === 'request' && resendSecondsLeft > 0)) return undefined
    const timer = window.setInterval(() => {
      setAccessSecondsLeft((value) => Math.max(0, value - 1))
      setResendSecondsLeft((value) => Math.max(0, value - 1))
    }, 1000)
    return () => window.clearInterval(timer)
  }, [accessFlow?.phase, resendSecondsLeft])

  useEffect(() => {
    if (!rescheduleState || rescheduleState.step !== 'pending') return undefined
    if (rescheduleSecondsLeft <= 0) {
      setRescheduleState(null)
      addMessage('assistant', 'Thời gian giữ tạm khung giờ mới đã hết. Lịch cũ của bạn vẫn được giữ nguyên.')
      return undefined
    }
    const timer = window.setInterval(() => setRescheduleSecondsLeft((value) => Math.max(0, value - 1)), 1000)
    return () => window.clearInterval(timer)
  }, [rescheduleState, rescheduleSecondsLeft])

  const changePerson = (field, value) => {
    setPerson((current) => ({ ...current, [field]: value }))
    setFormErrors((current) => ({ ...current, [field]: '' }))
  }

  const submitPerson = async (event) => {
    event.preventDefault()
    const errors = {}
    if (person.bookingName.trim().length < 2) errors.bookingName = 'Vui lòng nhập tên người đặt lịch.'
    if (recipient === 'other' && person.driverName.trim().length < 2) errors.driverName = 'Vui lòng nhập tên người lái thử.'
    if (!/^(0|\+84)[0-9\s.-]{8,12}$/.test(person.phone.trim())) errors.phone = 'Số điện thoại Việt Nam chưa đúng.'
    if (person.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(person.email)) errors.email = 'Email chưa đúng định dạng.'
    if (!person.hasLicense) errors.hasLicense = 'Cần xác nhận giấy phép lái xe trước khi tiếp tục.'
    setFormErrors(errors)
    if (Object.keys(errors).length) return

    // TODO [BACKEND]: Validate customer/driver identity, consentVersion,
    // privacyPolicyVersion and driving-licence declaration. Extend/validate the
    // existing hold; do not create a second hold for the same draft.
    setBackendError('')
    try {
      const saved = await saveBookingCustomer({ bookingId, version: bookingVersion, recipient, person })
      setBookingVersion(saved.version)
      setStage('review')
      setActiveView('ticket')
      addMessage('user', 'Tôi đã hoàn tất thông tin người lái.')
      reply('ViVi đã lưu phiếu tạm cho bạn. Bạn hãy kiểm tra lại thông tin và bấm “Xác nhận đặt lịch” nhé.')
    } catch (error) {
      reply(`Chưa thể lưu thông tin: ${error.message}`)
    }
  }

  const submitBooking = async () => {
    setSubmitting(true)
    // ĐÃ XONG: đặt lịch chạy thật qua confirmHeldBooking (POST /api/v1/chat,
    // action confirm_booking). Chống bấm trùng bằng ui_action_id sinh từ api/ids.js.
    // Contract tham chiếu giữ lại: response cần bookingCode, status,
    // assignedSalesRepresentative; 409/410 phải
    // return the user to live slot selection without losing customer form values.
    try {
      const actionKey = `${bookingId}:${bookingVersion}`
      const uiActionId = confirmActionIdsRef.current.get(actionKey) || actionId('confirm')
      confirmActionIdsRef.current.set(actionKey, uiActionId)
      const confirmed = await confirmHeldBooking({ bookingId, version: bookingVersion, uiActionId })
      confirmActionIdsRef.current.delete(actionKey)
      setSubmitting(false)
      setBookingCode(confirmed.booking_code)
      // Phiếu chỉ xuất hiện sau cinematic. Backend vẫn là nguồn xác nhận cuối cùng;
      // animation không tự tạo booking và không chạy nếu request ở trên thất bại.
      setSuccessCinematic(true)
    } catch (error) {
      setSubmitting(false)
      reply(`Chưa thể xác nhận lịch: ${error.message}`)
    }
  }

  const viewOptions = [
    ...(selectedCar ? [
      { id: 'car', label: 'Đổi mẫu xe', icon: CarProfile },
      ...(nearbyShowrooms.length ? [{ id: 'map', label: 'Showroom', icon: MapPin }] : []),
      ...(selectedShowroom ? [{ id: 'schedule', label: 'Lịch trống', icon: CalendarBlank }] : []),
      ...(stage === 'review' || stage === 'success' ? [{ id: 'ticket', label: 'Phiếu lịch', icon: CheckCircle }] : []),
    ] : []),
    ...(accessProfile ? [{ id: 'bookings', label: 'Lịch đã đặt', icon: CalendarBlank }] : []),
  ]

  const renderWorkspace = () => {
    if (activeView === 'bookings' && accessProfile) return <section className="booking-history"><div className="studio-schedule__heading"><span>Lịch đã đặt</span><h2>Mã lịch gần nhất</h2></div><div className="booking-history__list">{accessibleBookings.map((booking) => { const expanded = expandedBookingId === booking.id; const details = booking.id === accessProfile.bookingId ? accessProfile : null; return <div key={booking.id} className={expanded ? 'is-active is-expanded' : ''}><button type="button" onClick={() => { setExpandedBookingId(expanded ? '' : booking.id); if (!expanded) selectAccessibleBooking(booking) }}><strong>{booking.booking_code}</strong><small>{booking.start_at ? new Intl.DateTimeFormat('vi-VN', { weekday: 'long', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(booking.start_at)) : 'Lịch lái thử'}</small></button>{expanded && details && <div className="booking-history__details"><p><span>Mẫu xe</span>{details.vehicleName}</p><p><span>Showroom</span>{details.showroomName}<small>{details.showroomAddress}</small></p><p><span>Thời gian</span>{details.slotTime} · {details.slotDate}<button type="button" className="booking-history__reschedule" onClick={() => beginAccessibleReschedule(booking)} aria-label={`Đổi ngày giờ lịch ${booking.booking_code}`}><CalendarBlank size={18} weight="light" /></button></p>{rescheduleState?.step === 'pending' && <p className="booking-history__hold"><span>Khung giờ mới đang được giữ</span>Còn lại {Math.floor(rescheduleSecondsLeft / 60)}:{String(rescheduleSecondsLeft % 60).padStart(2, '0')}</p>}<p><span>Tư vấn viên</span>{details.advisorName}<small>{details.advisorPhone || 'Chưa có số điện thoại'}</small></p></div>}</div> })}</div></section>
    if (rescheduleState?.step === 'showroom') return <section className="studio-schedule"><div className="studio-schedule__heading"><span>Showroom hiện tại không còn lịch</span><h2>Chọn showroom khác</h2></div><div className="reschedule-left-grid">{rescheduleState.showrooms.map((showroom) => <button type="button" key={showroom.id} onClick={() => loadRescheduleSlots(rescheduleState.car, showroom)}><strong>{showroom.name}</strong><small>{showroom.address}</small></button>)}</div></section>
    if (rescheduleState?.step === 'schedule') return <SchedulePanel car={rescheduleState.car} showroom={rescheduleState.showroom} slots={groupSlots(rescheduleState.slots)} pendingSlot={null} onPick={(picked) => holdReschedule(rescheduleState.slots.find((slot) => slot.id === picked.slotId))} />
    if (rescheduleState?.step === 'pending') return <SchedulePanel car={rescheduleState.car} showroom={rescheduleState.showroom} slots={groupSlots(rescheduleState.slots)} pendingSlot={{ slotId: rescheduleState.slot.id }} onPick={(picked) => holdReschedule(rescheduleState.slots.find((slot) => slot.id === picked.slotId))} />
    if (rescheduleState?.step === 'confirm') return <section className="studio-schedule"><div className="studio-schedule__heading"><span>Đang chờ xác nhận</span><h2>Xác nhận lịch ở cửa sổ bên phải</h2></div></section>
    if (!selectedCar) return null
    if (activeView === 'map') return <BookingShowroomMap car={selectedCar} showrooms={nearbyShowrooms} selectedId={showroomId} onSelect={setShowroomId} onConfirm={chooseShowroom} userLocation={userLocation} />
    if (activeView === 'schedule' && selectedShowroom) return <SchedulePanel car={selectedCar} showroom={selectedShowroom} slots={slots} pendingSlot={pendingSlot} onPick={chooseSlot} />
    if (activeView === 'ticket' && selectedShowroom && selectedSlot) return <BookingTicket car={selectedCar} showroom={selectedShowroom} slot={selectedSlot} person={person} recipient={recipient} bookingCode={bookingCode} />
    return <VehiclePanel car={selectedCar} />
  }

  const showVehicleChoices = stage === 'need_car'

  if (bookingStatus === 'unavailable') {
    return (
      <main id="main-content" className="booking-unavailable">
        <Brand />
        <div>
          <span>Dịch vụ đặt lịch</span>
          <h1>Backend hiện không khả dụng.</h1>
          <p>Dữ liệu xe, showroom, lịch trống và thao tác giữ chỗ đều cần kết nối backend.</p>
          <button type="button" onClick={retry}>Thử kết nối lại</button>
          <Link to="/">Quay về trang chủ</Link>
        </div>
      </main>
    )
  }

  return (
    <main id="main-content" className={`agent-booking-page ${selectedCar && !workspaceHidden ? 'has-workspace' : 'is-agent-only'} ${stage === 'success' ? 'is-success' : ''} ${successCinematic ? 'is-cinematic' : ''}`}>
      <header className="booking-topbar booking-topbar--studio">
        <Link to="/"><ArrowLeft size={17} weight="light" /> Trang chủ</Link>
        <Brand />
        {/* TODO [BACKEND/SESSION — P0]: This claim is fully true only after the draft
            API restores recipient, vehicle, address, showroom, hold and stage. At
            present the browser stores only last-viewed vehicle and dismissal flags. */}
        <div><span /> Tiến trình được giữ trên thiết bị</div>
      </header>

      {(selectedCar || accessProfile) && workspaceHidden && (
        <button
          type="button"
          onClick={() => setWorkspaceHidden(false)}
          className="workspace-restore-button"
          style={{
            position: 'fixed',
            left: '37px',
            top: '117px',
            zIndex: 99,
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '7px',
            height: '38px',
            padding: '0 13px',
            borderRadius: '11px',
            background: '#ffffff',
            color: '#4a4d52',
            border: '1px solid rgba(0,0,0,0.05)',
            cursor: 'pointer',
            fontWeight: '620',
            fontSize: '0.73rem',
            boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
            transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.backgroundColor = '#20252b'
            e.currentTarget.style.color = '#ffffff'
            e.currentTarget.style.borderColor = '#20252b'
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.backgroundColor = '#ffffff'
            e.currentTarget.style.color = '#4a4d52'
            e.currentTarget.style.borderColor = 'rgba(0,0,0,0.05)'
          }}
        >
          <ArrowRight size={16} weight="bold" />
          <span style={{ fontSize: '0.73rem', fontWeight: '700', letterSpacing: '-0.01em' }}>Hiện bảng</span>
        </button>
      )}

      {!recipient && !resumePending && <RecipientModal onSelect={beginConversation} />}
      {resumePending && <ResumeModal onContinue={resumeConversation} onRestart={restartConversation} />}
      {successCinematic && selectedCar && (
        <BookingSuccessCinematic car={selectedCar} onComplete={completeBookingSuccess} />
      )}

      {stage === 'success' && selectedCar && selectedShowroom && selectedSlot ? (
        <div className="booking-success-layout">
          <div className="booking-success-documents">
            <VehiclePanel car={selectedCar} success3d />
            <BookingTicket car={selectedCar} showroom={selectedShowroom} slot={selectedSlot} person={person} recipient={recipient} bookingCode={bookingCode} compact />
          </div>
          <section className="vivi-studio vivi-studio--success">
            <div className="vivi-studio__head">
              <ViViAvatar />
              <div><strong>ViVi</strong><small><span /> Lịch đã được xác nhận</small></div>
            </div>
            <div className="vivi-success-copy">
              <div className="vivi-success-copy__status">
                <span><CheckCircle size={22} weight="regular" /></span>
                <p>Lịch lái thử đã được xác nhận</p>
              </div>
              <h1>Hẹn gặp bạn tại <span>{selectedShowroom.name}.</span></h1>
              <div className="vivi-success-copy__code"><small>Mã lịch</small><strong>{bookingCode}</strong></div>
              <p className="vivi-success-copy__note">Để tra cứu, bổ sung hoặc huỷ lịch, bạn chỉ cần cung cấp lại họ tên và số điện thoại đã đăng ký.</p>
              <div className="vivi-success-copy__actions"><button type="button" onClick={startLookup}>Tra cứu lịch này</button><Link to="/" onClick={() => window.sessionStorage.removeItem(BOOKING_UI_STATE_KEY)}>Về trang chủ</Link></div>
            </div>
          </section>
        </div>
      ) : (
        <div className={`booking-studio ${(selectedCar || accessProfile) && !workspaceHidden ? 'booking-studio--split' : 'booking-studio--agent'}`}>
          {(selectedCar || accessProfile) && !workspaceHidden && (
            <section className="booking-workspace">
              <div className="workspace-switcher" role="tablist" aria-label="Nội dung hỗ trợ đặt lịch">
                {viewOptions.map(({ id, label, icon: Icon }) => {
                  const active = activeView === id
                  // Tab "Mẫu xe" khi đang mở sẽ đóng vai trò nút đổi xe: bấm lần nữa mở bảng chọn.
                  const isCarTab = id === 'car'
                  return (
                    <button
                      type="button"
                      role="tab"
                      key={id}
                      aria-selected={active}
                      aria-haspopup={isCarTab ? 'dialog' : undefined}
                      title={isCarTab ? 'Bấm lần nữa để đổi mẫu xe' : undefined}
                      className={`${active ? 'is-active' : ''} ${isCarTab ? 'is-car-tab' : ''}`.trim()}
                      onClick={() => {
                        if (isCarTab && active) setSwitcherOpen(true)
                        else setActiveView(id)
                      }}
                    >
                      <Icon size={16} weight="light" /> {label}
                      {isCarTab && <CaretDown size={11} weight="bold" />}
                    </button>
                  )
                })}
                <button
                  type="button"
                  title="Ẩn bảng hỗ trợ"
                  className="workspace-switcher__close"
                  onClick={() => setWorkspaceHidden(true)}
                  style={{
                    marginLeft: 'auto',
                    border: 'none',
                    background: 'transparent',
                    color: '#92959a',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '0.78rem',
                    padding: '4px 8px',
                    borderRadius: '8px',
                    transition: 'color 0.2s',
                  }}
                  onMouseOver={(e) => e.currentTarget.style.color = '#ff4d4f'}
                  onMouseOut={(e) => e.currentTarget.style.color = '#92959a'}
                >
                  <X size={14} weight="bold" /> Ẩn bảng
                </button>
              </div>
              <div className="booking-workspace__content" key={activeView}>{renderWorkspace()}</div>
            </section>
          )}

          <section className="vivi-studio">
            <div className="vivi-studio__head">
              <ViViAvatar />
              <div><strong>ViVi</strong><small><span /> Trợ lý đặt lịch lái thử</small></div>
              <button type="button" onClick={startLookup}>Tra cứu lịch</button>
            </div>

            <div className="vivi-studio__messages" ref={messagesRef} aria-live="polite">
              {resumePending ? (
                <div className="vivi-studio__empty"><ViViAvatar /><p>Bạn đang có một phiên đặt lịch đang dở.</p></div>
              ) : messages.length ? messages.map((message) => <AgentMessage key={message.id} message={message} />) : (
                <div className="vivi-studio__empty"><ViViAvatar /><p>Chọn người lái thử để ViVi bắt đầu.</p></div>
              )}
              {agentTyping && (
                <div className="vivi-message vivi-message--assistant">
                  <ViViAvatar compact />
                  <div className="vivi-typing" aria-label={checkingVehicleName ? `ViVi đang kiểm tra ${checkingVehicleName}` : 'ViVi đang trả lời'}>
                    <span />
                    <span />
                    <span />
                    {checkingVehicleName && <small>ViVi đang kiểm tra {checkingVehicleName}…</small>}
                  </div>
                </div>
              )}
            </div>

            <div className="vivi-studio__composer">
              {backendError && <p className="booking-api-error" role="alert">{backendError}</p>}
              {resumePending ? (
                null
              ) : accessFlow && accessFlow.phase !== 'confirm_cancel' ? (
                <BookingAccessPanel
                  phase={accessFlow.phase}
                  value={accessValue}
                  onChange={changeAccessValue}
                  onRequest={requestAccessOtp}
                  onVerify={verifyAccessOtp}
                  onResend={requestAccessOtp}
                  onCancel={cancelAccessOtp}
                  secondsLeft={accessSecondsLeft}
                  resendLeft={resendSecondsLeft}
                  error={accessError}
                  busy={accessBusy}
                  profile={accessProfile}
                  onProfileChange={changeAccessProfile}
                  onProfileSave={saveAccessProfile}
                  onBookingCancel={confirmCancellation}
                />
              ) : <>
              {showVehicleChoices && (
                <div className="agent-vehicle-choices" aria-label="Mẫu xe gợi ý">
                  {featuredChoices.map((car) => (
                    <button type="button" key={car.id} onClick={() => chooseCar(car)}>
                      <span>{car.name}</span>
                    </button>
                  ))}
                </div>
              )}

              <ContextualChoices
                stage={stage}
                car={selectedCar}
                locationSuggestions={locationSuggestions}
                showrooms={nearbyShowrooms}
                slots={slots}
                onResolveArea={resolveSuggestedArea}
                onShowroom={chooseShowroom}
                onSlot={chooseSlot}
              />

              {(stage === 'need_car' || stage === 'need_address') && (
                <div className="vivi-capabilities">
                  {stage === 'need_car' && (
                    <button type="button" onClick={() => setSwitcherOpen(true)} aria-haspopup="dialog">
                      <CarProfile size={14} weight="light" style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                      Xem tất cả {cars.length} mẫu
                    </button>
                  )}
                  {stage === 'need_address' && (
                    <button type="button" onClick={requestUserLocation}>
                      <NavigationArrow size={14} weight="light" style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                      Định vị hiện tại
                    </button>
                  )}
                  <button type="button" onClick={startLookup}>
                    <CalendarBlank size={14} weight="light" style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                    Tra cứu lịch đã đặt
                  </button>
                  {selectedCar && (
                    <button type="button" onClick={() => setSwitcherOpen(true)} aria-haspopup="dialog">
                      <CarProfile size={14} weight="light" style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                      Đổi mẫu xe khác
                    </button>
                  )}
                </div>
              )}

              {timeLeft && (stage === 'collect_info' || stage === 'review') && (
                <div className="vivi-hold-timer" style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  margin: '0 0 16px',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  background: 'rgba(239, 107, 7, 0.08)',
                  border: '1px solid rgba(239, 107, 7, 0.2)',
                  color: '#e25c00',
                  fontSize: '0.72rem',
                  fontWeight: '600'
                }}>
                  <span>Khung giờ đang giữ tạm thời. Còn lại: <strong style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{timeLeft}</strong></span>
                </div>
              )}

              {stage === 'collect_info' ? (
                <CustomerForm recipient={recipient} value={person} errors={formErrors} onChange={changePerson} onSubmit={submitPerson} />
              ) : stage === 'review' ? (
                <div className="vivi-review-actions">
                  <button type="button" onClick={submitBooking} disabled={submitting}>{submitting ? 'Đang giữ lịch' : 'Xác nhận đặt lịch'} <Check size={16} weight="light" /></button>
                  <button type="button" onClick={() => { setStage('collect_info'); setActiveView('schedule') }}>Chỉnh lại thông tin</button>
                </div>
              ) : (
                <form className="vivi-prompt" onSubmit={handlePrompt} aria-busy={composerDisabled}>
                  <label htmlFor="vivi-booking-prompt">Nhắn cho ViVi</label>
                  <div>
                    <textarea id="vivi-booking-prompt" rows="2" value={draft} maxLength={CHAT_MESSAGE_MAX_LENGTH} disabled={composerDisabled} onChange={(event) => setDraft(event.target.value)} placeholder={composerDisabled ? 'ViVi đang trả lời...' : stage === 'need_address' || stage === 'need_ward' ? 'Ví dụ: Phường Bến Nghé, TP. Hồ Chí Minh' : 'Nhập mẫu xe, địa chỉ, showroom hoặc thời gian…'} onKeyDown={(event) => {
                      if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault()
                        if (!composerDisabled) event.currentTarget.form?.requestSubmit()
                      }
                    }} />
                    <button type="submit" aria-label="Gửi tin nhắn" disabled={composerDisabled || !draft.trim()}><PaperPlaneTilt size={18} weight="light" /></button>
                  </div>
                  <small>Enter để gửi · Shift + Enter để xuống dòng · {draft.length.toLocaleString('vi-VN')}/{CHAT_MESSAGE_MAX_LENGTH.toLocaleString('vi-VN')}</small>
                </form>
              )}
              </>}
            </div>
          </section>
        </div>
      )}

      {switcherOpen && (
        <VehicleSwitcher
          cars={cars}
          currentId={selectedCarId}
          onSelect={pickCarFromSwitcher}
          onClose={() => setSwitcherOpen(false)}
        />
      )}

      {confirmSlotOpen && selectedCar && selectedShowroom && pendingSlot && (
        <div className="slot-confirm-modal" role="dialog" aria-modal="true" aria-labelledby="slot-confirm-title">
          <div>
            <button type="button" onClick={() => setConfirmSlotOpen(false)} aria-label="Đóng"><X size={17} weight="light" /></button>
            <div className="slot-confirm-summary" aria-hidden="true">
              <span>{pendingSlot.dateLabel}</span>
              <strong>{pendingSlot.time}</strong>
            </div>
            <p>Xác nhận khung giờ</p>
            <h2 id="slot-confirm-title">Bạn sẽ lái thử {selectedCar.name}</h2>
            <dl>
              <div><dt>Showroom</dt><dd>{selectedShowroom.name}</dd></div>
              <div><dt>Thời gian</dt><dd>{pendingSlot.time} · {pendingSlot.dateLabel}</dd></div>
              <div><dt>Mẫu xe</dt><dd>{selectedCar.name} đã được giữ cho slot này</dd></div>
            </dl>
            <div className="slot-confirm-actions"><button type="button" onClick={confirmSlot}>Xác nhận khung giờ</button><button type="button" onClick={() => setConfirmSlotOpen(false)}>Quay lại chọn lịch</button></div>
          </div>
        </div>
      )}
      {rescheduleState?.step === 'confirm' && <RescheduleConfirmModal state={rescheduleState} secondsLeft={rescheduleSecondsLeft} onConfirm={confirmReschedule} onBack={() => setRescheduleState((current) => ({ ...current, step: 'pending' }))} busy={accessBusy} />}
      {accessFlow?.phase === 'confirm_cancel' && accessProfile && (
        <CancellationConfirmModal
          profile={accessProfile}
          car={cars.find((car) => car.name === accessProfile.vehicleName) || null}
          onConfirm={confirmCancellation}
          onClose={cancelAccessOtp}
          busy={accessBusy}
          error={accessError}
        />
      )}
    </main>
  )
}
