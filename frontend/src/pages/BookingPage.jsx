import { useEffect, useMemo, useRef, useState } from 'react'
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
import { carGroups, cars, getCar } from '../data/cars'
import { viviAvatar } from '../data/media'

const driveCars = cars
const featuredChoices = ['vf3', 'vf5', 'vf6', 'vf7', 'vf-mpv-7'].map(getCar).filter(Boolean)

// BACKEND HANDOFF: This file is currently a complete frontend prototype/state
// machine with deterministic fixtures. Replace each TODO [BACKEND/*] boundary,
// not the visual components. Canonical contracts and failure behaviour live in
// ../../BACKEND_HANDOFF.md.

// TODO [BACKEND]: Replace this inventory-aware showroom fixture with
// GET /api/v1/test-drive/showrooms?vehicleId=&lat=&lng=. Backend must rank
// exact vehicle availability first, then travel distance from geocoded address.
// Each result needs id, coordinates, address, distanceMeters, openingStatus,
// availableVehicleIds and accessibility metadata. Sales staff is assigned only
// after booking creation; do not treat the fixture's staff fields as authoritative.
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

// TODO [BACKEND/GEOCODING]: Remove this limited alias table after connecting an
// address service that returns normalized province/ward ids plus lat/lng and a
// confidence score. Low-confidence or province-only input must keep stage=need_ward.
const provinceAliases = [
  { name: 'TP. Hồ Chí Minh', aliases: ['hồ chí minh', 'ho chi minh', 'tp hcm', 'tphcm', 'sài gòn', 'sai gon'] },
  { name: 'Hà Nội', aliases: ['hà nội', 'ha noi'] },
  { name: 'Đà Nẵng', aliases: ['đà nẵng', 'da nang'] },
  { name: 'Bình Dương', aliases: ['bình dương', 'binh duong'] },
]

const normalize = (value = '') => value
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .replace(/đ/g, 'd')
  .toLowerCase()
  .replace(/[^a-z0-9\s]/g, ' ')
  .replace(/\s+/g, ' ')
  .trim()

const findProvince = (value) => {
  const normalized = normalize(value)
  return provinceAliases.find((province) =>
    province.aliases.some((alias) => normalized.includes(normalize(alias))),
  )?.name || ''
}

const hasLocalUnit = (value) => /\b(phường|phuong|xã|xa|thị trấn|thi tran)\b/i.test(value)

const findCarFromText = (value) => {
  const normalized = normalize(value).replace(/vinfast/g, '').trim()
  const compact = normalized.replace(/\s/g, '')
  return [...driveCars].sort((a, b) => b.name.length - a.name.length).find((car) => {
    const candidates = [car.name, car.navName, car.id].map(normalize)
    return candidates.some((candidate) =>
      normalized.includes(candidate) || compact.includes(candidate.replace(/\s/g, '')),
    )
  })
}

function createSlots(showroomId, carId) {
  // TODO [BACKEND]: Replace generated slots with
  // GET /api/v1/test-drive/slots?showroomId=&vehicleId=. Every slot needs an
  // inventorySlotId proving the requested vehicle is available at that time,
  // startAt/endAt in ISO-8601, timezone=Asia/Ho_Chi_Minh, capacity/status and
  // holdExpiresAt when held. Never derive availability in the browser.
  const times = ['08:30', '09:45', '13:30', '15:00', '16:30']
  return Array.from({ length: 5 }, (_, dayIndex) => {
    const date = new Date()
    date.setDate(date.getDate() + dayIndex + 1)
    const value = date.toISOString().slice(0, 10)
    const dateLabel = new Intl.DateTimeFormat('vi-VN', {
      weekday: 'short',
      day: '2-digit',
      month: '2-digit',
    }).format(date)
    return {
      value,
      dateLabel,
      times: times.filter((_, timeIndex) => (dayIndex + timeIndex + showroomId.length + carId.length) % 4 !== 0),
    }
  })
}

function RecipientModal({ onSelect }) {
  return (
    <div className="recipient-modal" role="dialog" aria-modal="true" aria-labelledby="recipient-title">
      <div className="recipient-modal__panel">
        <span className="recipient-modal__mark"><User size={24} weight="light" /></span>
        <p>Trước khi bắt đầu</p>
        <h1 id="recipient-title">Bạn đặt lịch lái thử cho ai?</h1>
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

function AgentMessage({ message }) {
  return (
    <div className={`vivi-message vivi-message--${message.role}`}>
      {message.role === 'assistant' && <ViViAvatar compact />}
      <div><p>{message.text}</p></div>
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

function ContextualChoices({ stage, car, address, showrooms, slots, onResolveArea, onShowroom, onSlot }) {
  if (!car) return null

  if (stage === 'need_address' || stage === 'need_ward') {
    // TODO [BACKEND]: Populate these suggestions from availability-aware showroom
    // results for the selected vehicle, not from a nationwide static directory.
    const areas = showroomDirectory
      .filter((showroom) => showroom.models.includes(car.id) && (!address.province || showroom.province === address.province))
      .filter((showroom, index, entries) => entries.findIndex((item) => item.province === showroom.province) === index)
      .slice(0, 4)

    return (
      <div className="agent-context" aria-label="Showroom có sẵn mẫu xe">
        <div className="agent-context__heading">
          <span>Điểm có xe lái thử</span>
          <small>Chọn nhanh một khu vực hoặc tiếp tục nhập địa chỉ chi tiết</small>
        </div>
        <div className="agent-context__rail">
          {areas.map((showroom) => (
            <button type="button" key={showroom.id} onClick={() => onResolveArea(showroom)}>
              <span><MapPin size={16} weight="light" /></span>
              <strong>{showroom.name.replace('VinFast ', '')}</strong>
              <small>{showroom.province} · Có {car.name}</small>
            </button>
          ))}
        </div>
      </div>
    )
  }

  if (stage === 'choose_showroom' && showrooms.length) {
    return (
      <div className="agent-context" aria-label="Chọn showroom trong cuộc trò chuyện">
        <div className="agent-context__heading"><span>Showroom phù hợp</span><small>Đã ưu tiên có xe trước, khoảng cách sau</small></div>
        <div className="agent-context__rail">
          {showrooms.map((showroom) => (
            <button type="button" key={showroom.id} onClick={() => onShowroom(showroom)}>
              <span><MapPin size={16} weight="light" /></span>
              <strong>{showroom.name.replace('VinFast ', '')}</strong>
              <small>{String(showroom.distance).replace('.', ',')} km · Có {car.name}</small>
            </button>
          ))}
        </div>
      </div>
    )
  }

  if (stage === 'choose_slot' && slots.length) {
    const quickSlots = slots.flatMap((day) => day.times.slice(0, 1).map((time) => ({
      date: day.value,
      dateLabel: day.dateLabel,
      time,
    }))).slice(0, 4)
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

function VehicleSwitcher({ currentId, onSelect, onClose }) {
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

function VehiclePanel({ car }) {
  return (
    <section className="studio-vehicle" aria-label={`Mẫu xe ${car.name}`}>
      <div className="studio-vehicle__ambient" aria-hidden="true" />
      <div className="studio-vehicle__heading">
        <span>Mẫu xe đang giữ</span>
        <strong>{car.name}</strong>
        <small>{car.body} · {car.seats}</small>
      </div>
      <div className="studio-vehicle__stage" key={car.id}>
        <VehicleShot car={car} className="studio-vehicle__image" eager />
      </div>
      <div className="studio-vehicle__specs">
        {car.specs.slice(0, 3).map((spec) => (
          <div key={spec.label}><strong>{spec.value}</strong><span>{spec.label}</span></div>
        ))}
      </div>
      <Link to={`/cars/${car.id}`}>Xem lại thông tin xe <ArrowRight size={15} weight="light" /></Link>
    </section>
  )
}

function ShowroomMap({ car, showrooms, selectedId, onSelect }) {
  const selected = showrooms.find((showroom) => showroom.id === selectedId) || showrooms[0]

  // TODO [BACKEND/MAPS]: Replace only the canvas/drawing with the chosen map SDK.
  // Preserve this list + selection model. Markers use backend lat/lng; distance and
  // route duration must come from geocoding/routing, never x/y presentation values.
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
            onClick={() => onSelect(showroom)}
          >
            <span>{index + 1}</span>
            <span><strong>{showroom.name}</strong><small>{showroom.address}</small></span>
            <em>{String(showroom.distance).replace('.', ',')} km</em>
          </button>
        ))}
      </aside>

      <div className="studio-map__canvas">
        <div className="studio-map__search">
          <MagnifyingGlass size={18} weight="regular" />
          <span><strong>Showroom có {car.name}</strong><small>Gần vị trí bạn vừa cung cấp</small></span>
        </div>
        <div className="studio-map__filters" aria-hidden="true">
          <span>Đang mở cửa</span><span>Có xe lái thử</span>
        </div>
        <svg className="studio-map__drawing" viewBox="0 0 900 620" preserveAspectRatio="none" aria-hidden="true">
          <rect width="900" height="620" fill="#e8eaed" />
          <path className="map-water" d="M-20 505C160 450 226 525 380 475s245-12 360-77 153-36 190-12v254H-20Z" />
          <path className="map-park" d="M40 45h245v150H40zM664 34h210v116H664zM604 446h230v132H604z" />
          <path className="map-block" d="M322 32h214v120H322zM78 258h190v132H78zM625 216h222v164H625zM333 410h178v154H333z" />
          <path className="map-road map-road--major" d="M-30 430C160 338 230 394 384 292S620 204 945 88" />
          <path className="map-road map-road--major" d="M104-40C172 116 264 134 337 251s142 220 264 410" />
          <path className="map-road" d="M-40 176c194 66 318 17 438 79s237 178 550 124" />
          <path className="map-road" d="M569-30c-30 151 36 234 132 315s107 176 91 375" />
          <path className="map-road map-road--minor" d="M18 318h286M356 92h244M180 548h322M508 488h398" />
          <text x="350" y="282">Đường trung tâm</text>
          <text x="630" y="186">Khu đô thị</text>
          <text x="92" y="232">Công viên</text>
        </svg>
        <span className="studio-map__user"><span /> Vị trí của bạn</span>
        {showrooms.map((showroom, index) => (
          <button
            type="button"
            key={showroom.id}
            className={selectedId === showroom.id ? 'is-active' : ''}
            style={{ '--marker-x': `${showroom.x}%`, '--marker-y': `${showroom.y}%` }}
            onClick={() => onSelect(showroom)}
            aria-label={`Chọn ${showroom.name}`}
          >
            <span>{index + 1}</span>
          </button>
        ))}
        <div className="studio-map__controls" aria-label="Điều khiển bản đồ mô phỏng">
          {/* TODO [BACKEND/MAPS]: Nối các nút này với SDK bản đồ và geocoding thực tế. */}
          <button type="button" aria-label="Phóng to bản đồ"><Plus size={17} weight="regular" /></button>
          <button type="button" aria-label="Thu nhỏ bản đồ"><Minus size={17} weight="regular" /></button>
          <button type="button" aria-label="Về vị trí của tôi"><Crosshair size={17} weight="regular" /></button>
        </div>
        {selected && (
          <div className="studio-map__preview">
            <span><strong>{selected.name}</strong><small>{selected.address}</small></span>
            <button type="button" onClick={() => onSelect(selected)} aria-label={`Chọn ${selected.name}`}>
              <NavigationArrow size={17} weight="fill" />
            </button>
          </div>
        )}
      </div>
    </section>
  )
}

function SchedulePanel({ car, showroom, slots, pendingSlot, onPick }) {
  return (
    <section className="studio-schedule" aria-label="Lịch lái thử còn trống">
      <div className="studio-schedule__heading">
        <span>Lịch có đúng mẫu xe</span>
        <h2>{car.name} tại {showroom.name}</h2>
        <p>Mỗi khung giờ bên dưới đã được ghép với xe lái thử đang sẵn sàng.</p>
      </div>
      <div className="studio-schedule__grid">
        {slots.map((day) => (
          <article key={day.value}>
            <header><CalendarBlank size={18} weight="light" /><strong>{day.dateLabel}</strong></header>
            <div>
              {day.times.map((time) => {
                const active = pendingSlot?.date === day.value && pendingSlot?.time === time
                return (
                  <button
                    type="button"
                    className={active ? 'is-active' : ''}
                    key={time}
                    onClick={() => onPick({ date: day.value, dateLabel: day.dateLabel, time })}
                  >
                    <Clock size={15} weight="light" /> {time}
                  </button>
                )
              })}
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

function BookingTicket({ car, showroom, slot, person, recipient, bookingCode, compact = false }) {
  // TODO [BACKEND/BOOKING]: In success/retrieval mode render an immutable booking
  // response. `assignedSalesRepresentative` belongs to the booking response and may
  // not be copied from the showroom listing. Mask phone/email on lookup as required.
  const rows = [
    ['Người đặt lịch', person.bookingName],
    ['Người lái thử', recipient === 'other' ? person.driverName : person.bookingName],
    ['Điện thoại', person.phone],
    ['Email', person.email || 'Không đăng ký nhận email'],
    ['Mẫu xe', car.name],
    ['Showroom', showroom.name],
    ['Thời gian', `${slot.time} · ${slot.dateLabel}`],
    ['Tư vấn viên', `${showroom.staff} · ${showroom.staffPhone}`],
  ]

  return (
    <section className={`studio-ticket ${compact ? 'studio-ticket--compact' : ''}`}>
      <header>
        <span>{bookingCode ? 'Lịch lái thử đã xác nhận' : 'Kiểm tra trước khi đặt lịch'}</span>
        {bookingCode && <strong>{bookingCode}</strong>}
      </header>
      <div className="studio-ticket__vehicle">
        <VehicleShot car={car} />
        <span><strong>{car.name}</strong><small>{car.body}</small></span>
      </div>
      <dl>
        {rows.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
      </dl>
      <p><CheckCircle size={16} weight="fill" /> Đã xác nhận có giấy phép lái xe phù hợp.</p>
    </section>
  )
}

function CustomerForm({ recipient, value, errors, onChange, onSubmit }) {
  // TODO [BACKEND/PRIVACY]: Submit these PII fields only over TLS with a server-known
  // consentVersion and privacyPolicyVersion. Do not mirror name/phone/email into
  // localStorage, sessionStorage, analytics payloads or agent logs.
  return (
    <form className="vivi-customer-form" onSubmit={onSubmit} noValidate>
      <div className="vivi-customer-form__grid">
        <label>
          <span>{recipient === 'other' ? 'Tên người đặt lịch' : 'Họ và tên'}</span>
          <input value={value.bookingName} onChange={(event) => onChange('bookingName', event.target.value)} />
          {errors.bookingName && <small role="alert">{errors.bookingName}</small>}
        </label>
        {recipient === 'other' && (
          <label>
            <span>Tên người lái thử</span>
            <input value={value.driverName} onChange={(event) => onChange('driverName', event.target.value)} />
            {errors.driverName && <small role="alert">{errors.driverName}</small>}
          </label>
        )}
        <label>
          <span>Số điện thoại</span>
          <input type="tel" placeholder="09xx xxx xxx" value={value.phone} onChange={(event) => onChange('phone', event.target.value)} />
          {errors.phone && <small role="alert">{errors.phone}</small>}
        </label>
        <label>
          <span>Email</span>
          <input type="email" placeholder="tenban@example.com" value={value.email} onChange={(event) => onChange('email', event.target.value)} />
          {errors.email && <small role="alert">{errors.email}</small>}
        </label>
      </div>
      <label className={`license-check ${errors.hasLicense ? 'has-error' : ''}`}>
        <input type="checkbox" checked={value.hasLicense} onChange={(event) => onChange('hasLicense', event.target.checked)} />
        <span><Check size={14} weight="bold" /></span>
        <p>Tôi xác nhận người lái thử <strong>có giấy phép lái xe</strong> phù hợp với mẫu xe đăng ký.</p>
      </label>
      {errors.hasLicense && <small className="vivi-customer-form__license-error" role="alert">{errors.hasLicense}</small>}
      <button type="submit">Tạo phiếu để kiểm tra <ArrowRight size={16} weight="light" /></button>
    </form>
  )
}

export function BookingPage() {
  // UX state machine (server should return/validate the same nextStage values):
  // idle -> need_car -> need_address -> need_ward -> choose_showroom ->
  // choose_slot -> collect_info -> review -> success. `lookup` is a side flow.
  // The browser may render optimistically, but inventory holds and terminal booking
  // state are always server-authoritative. Full transition table: BACKEND_HANDOFF.md.
  const [searchParams] = useSearchParams()
  // TODO [BACKEND/SESSION]: Accept only a catalogue id from ?car=. When a draftId
  // exists, restore its server-side state first and use recentCar only as fallback.
  const routeCar = getCar(searchParams.get('car'))
  const recentCar = getCar(window.sessionStorage.getItem('vinfast:last-viewed-car'))
  const initialCar = routeCar || recentCar || null
  const [recipient, setRecipient] = useState('')
  const [selectedCarId, setSelectedCarId] = useState(initialCar?.id || '')
  const [stage, setStage] = useState('idle')
  const [activeView, setActiveView] = useState(initialCar ? 'car' : 'agent')
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [agentTyping, setAgentTyping] = useState(false)
  const [address, setAddress] = useState({ province: '', detail: '' })
  const [nearbyShowrooms, setNearbyShowrooms] = useState([])
  const [showroomId, setShowroomId] = useState('')
  const [pendingSlot, setPendingSlot] = useState(null)
  const [selectedSlot, setSelectedSlot] = useState(null)
  const [confirmSlotOpen, setConfirmSlotOpen] = useState(false)
  const [switcherOpen, setSwitcherOpen] = useState(false)
  const [person, setPerson] = useState({ bookingName: '', driverName: '', phone: '', email: '', hasLicense: false })
  const [formErrors, setFormErrors] = useState({})
  const [bookingCode, setBookingCode] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const messagesRef = useRef(null)
  const timersRef = useRef([])

  const selectedCar = getCar(selectedCarId)
  // TODO [BACKEND]: Resolve these from fetched state/query caches. A production slot
  // must include inventorySlotId; the UI's date/time tuple is display-only.
  const selectedShowroom = showroomDirectory.find((showroom) => showroom.id === showroomId)
  const slots = useMemo(
    () => selectedShowroom && selectedCar ? createSlots(selectedShowroom.id, selectedCar.id) : [],
    [selectedShowroom, selectedCar],
  )

  useEffect(() => () => timersRef.current.forEach((timer) => window.clearTimeout(timer)), [])
  useEffect(() => {
    messagesRef.current?.scrollTo({ top: messagesRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, stage, agentTyping])

  const addMessage = (role, text) => {
    // TODO [BACKEND/AGENT]: Use server message ids and timestamps. Store structured
    // cards/actions separately from display text so UI choices stay deterministic.
    setMessages((current) => [...current, { id: `${Date.now()}-${current.length}`, role, text }])
  }

  const reply = (text, delay = 420) => {
    // TODO [BACKEND/AGENT]: Replace this cosmetic delay with streamed message state
    // from POST /api/v1/booking-agent/messages (SSE or fetch stream). Cancel the
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
      reply(`Tôi đã giữ lại ${car.name}, mẫu xe bạn vừa xem gần nhất. Hãy cho tôi địa chỉ theo phường hoặc xã và tỉnh/thành phố để tìm showroom có đúng mẫu xe này. Ví dụ: “Phường Bến Nghé, TP. Hồ Chí Minh”.`, 520)
    } else {
      setStage('need_car')
      setActiveView('agent')
      reply('Trước tiên, bạn muốn lái thử mẫu xe nào? Bạn có thể chọn một mẫu ngay phía trên ô nhập hoặc nhắn tên xe cho tôi.', 520)
    }
  }

  const chooseCar = (car, fromPrompt = false) => {
    setSelectedCarId(car.id)
    window.sessionStorage.setItem('vinfast:last-viewed-car', car.id)
    if (!fromPrompt) addMessage('user', `Tôi muốn lái thử ${car.name}.`)
    setStage('need_address')
    setActiveView('car')
    reply(`Đã chọn ${car.name}. Hãy cho tôi địa chỉ cụ thể theo phường hoặc xã và tỉnh/thành phố để ưu tiên showroom có xe gần bạn nhất.`)
  }

  // Đổi mẫu xe giữa chừng: giữ lại địa chỉ, showroom và thông tin người lái đã nhập,
  // chỉ mở lại bước chọn khung giờ vì lịch luôn được ghép theo đúng mẫu xe.
  const switchCar = (car) => {
    setSwitcherOpen(false)
    if (!car || car.id === selectedCarId) return

    setSelectedCarId(car.id)
    window.sessionStorage.setItem('vinfast:last-viewed-car', car.id)
    setPendingSlot(null)
    setSelectedSlot(null)
    setConfirmSlotOpen(false)
    addMessage('user', `Tôi muốn đổi sang ${car.name}.`)

    // TODO [BACKEND]: Khi đổi xe phải nhả chỗ giữ cũ và kiểm tra lại tồn xe:
    // DELETE /api/v1/test-drive/holds/{holdId} rồi
    // GET /api/v1/test-drive/showrooms?vehicleId={car.id}&province=… để lấy danh sách mới.
    const matches = address.province
      ? showroomDirectory
        .filter((showroom) => showroom.province === address.province && showroom.models.includes(car.id))
        .sort((a, b) => a.distance - b.distance)
        .slice(0, 4)
      : []
    setNearbyShowrooms(matches)

    const keptShowroom = matches.find((showroom) => showroom.id === showroomId)
    if (keptShowroom) {
      setStage('choose_slot')
      setActiveView('schedule')
      reply(`Đã đổi sang ${car.name}. Tôi vẫn giữ ${keptShowroom.name}, nhưng khung giờ phải chọn lại để ghép đúng xe mới.`)
      return
    }

    setShowroomId('')
    if (matches.length) {
      setStage('choose_showroom')
      setActiveView('map')
      reply(`Đã đổi sang ${car.name}. Showroom cũ không có sẵn mẫu này, tôi đã lọc lại ${matches.length} điểm quanh “${address.detail}” — bạn chọn giúp tôi một điểm nhé.`)
      return
    }

    setStage('need_address')
    setActiveView('car')
    reply(`Đã đổi sang ${car.name}. Bạn cho tôi lại địa chỉ theo phường hoặc xã và tỉnh/thành phố để tìm showroom có sẵn mẫu này.`)
  }

  const resolveShowrooms = (province, detail) => {
    // TODO [BACKEND/GEOCODING + INVENTORY]: 1) normalize detail to administrative
    // ids/lat/lng; 2) query showrooms with selected vehicle availability; 3) rank by
    // exact vehicle first, then travel distance; 4) return at most four initial hits.
    const matches = showroomDirectory
      .filter((showroom) => showroom.province === province && showroom.models.includes(selectedCar.id))
      .sort((a, b) => a.distance - b.distance)
      .slice(0, 4)
    setAddress({ province, detail })
    setNearbyShowrooms(matches)
    setStage('choose_showroom')
    setActiveView('map')
    if (matches.length) {
      reply(`Tôi tìm thấy ${matches.length} showroom có ${selectedCar.name}, đã xếp theo khoảng cách từ “${detail}”. Hãy chọn một điểm trên bản đồ hoặc nhắn tên showroom bạn muốn.`)
    } else {
      reply(`Hiện chưa có showroom nào tại ${province} xác nhận sẵn ${selectedCar.name}. Bạn có thể gửi một khu vực lân cận để tôi kiểm tra tiếp.`)
    }
  }

  // Bảng chọn xe dùng chung cho lần chọn đầu tiên và cho việc đổi xe giữa chừng.
  const pickCarFromSwitcher = (car) => {
    setSwitcherOpen(false)
    if (!selectedCarId) chooseCar(car)
    else switchCar(car)
  }

  const resolveSuggestedArea = (showroom) => {
    addMessage('user', `Tìm quanh ${showroom.address}.`)
    resolveShowrooms(showroom.province, showroom.address)
  }

  const chooseShowroom = (showroom, fromPrompt = false) => {
    // TODO [BACKEND]: Persist showroomId on the draft, then fetch live slots for
    // showroomId + vehicleId. If availability changed, remain on choose_showroom and
    // refresh the cards/map instead of advancing to a blank schedule.
    if (!fromPrompt) addMessage('user', `Tôi chọn ${showroom.name}.`)
    setShowroomId(showroom.id)
    setStage('choose_slot')
    setActiveView('schedule')
    reply(`${showroom.name} đã được chọn. Các khung giờ bên trái đều đang có đúng ${selectedCar.name}. Bạn có thể bấm trực tiếp hoặc nhắn ngày, giờ mong muốn.`)
  }

  const chooseSlot = (slot) => {
    setPendingSlot(slot)
    setConfirmSlotOpen(true)
  }

  const confirmSlot = () => {
    // TODO [BACKEND/HOLD]: POST /api/v1/test-drive/holds with draftId,
    // inventorySlotId and vehicleId here. Advance only after receiving holdId and
    // holdExpiresAt. On 409 refresh slots; on 410 return to choose_slot.
    setSelectedSlot(pendingSlot)
    setConfirmSlotOpen(false)
    addMessage('user', `Tôi xác nhận ${pendingSlot.time}, ${pendingSlot.dateLabel}.`)
    setStage('collect_info')
    reply('Tôi đã giữ tạm khung giờ này. Vui lòng điền thông tin ngay trong cuộc trò chuyện; dữ liệu chỉ được gửi sau khi bạn xác nhận đặt lịch cuối cùng.')
  }

  const handlePrompt = (event) => {
    event.preventDefault()
    const value = draft.trim()
    if (!value) return
    setDraft('')
    addMessage('user', value)

    // TODO [BACKEND]: Replace local intent/entity parsing below with
    // POST /api/v1/booking-agent/messages. Return structured nextStage plus
    // extracted vehicle, administrative address, showroom and inventory slot.

    if (stage === 'need_car') {
      const car = findCarFromText(value)
      if (car) chooseCar(car, true)
      else reply('Tôi chưa nhận ra mẫu xe trong tin nhắn. Hãy thử nhập “VF 6”, “VF 8 thế hệ mới” hoặc chọn một ảnh xe phía trên ô nhập.')
      return
    }

    if (stage === 'need_address' || stage === 'need_ward') {
      const province = findProvince(value) || address.province
      const detailed = hasLocalUnit(value)
      if (!province) {
        reply('Tôi cần cả tỉnh hoặc thành phố. Bạn có thể nhập theo mẫu: “Phường Hải Châu, Đà Nẵng”.')
      } else if (!detailed) {
        setAddress({ province, detail: value })
        setStage('need_ward')
        reply(`Tôi đã ghi nhận ${province}. Bạn cho tôi thêm tên phường hoặc xã để không hiển thị tràn lan toàn bộ showroom trong khu vực nhé.`)
      } else {
        resolveShowrooms(province, findProvince(value) ? value : `${value}, ${province}`)
      }
      return
    }

    if (stage === 'choose_showroom') {
      const normalized = normalize(value)
      const showroom = nearbyShowrooms.find((item) => {
        const full = normalize(item.name)
        const short = normalize(item.name.replace('VinFast', ''))
        return normalized.includes(full) || normalized.includes(short)
      })
      if (showroom) chooseShowroom(showroom, true)
      else reply(`Tôi chưa khớp được showroom đó với danh sách đang có ${selectedCar.name}. Hãy chọn một điểm được đánh số trên bản đồ hoặc nhập đúng tên trong danh sách.`)
      return
    }

    if (stage === 'choose_slot') {
      const normalized = normalize(value)
      const match = slots.flatMap((day) => day.times.map((time) => ({ ...day, time })))
        .find((slot) => normalized.includes(normalize(slot.time)) || normalized.includes(normalize(slot.dateLabel)))
      if (match) chooseSlot({ date: match.value, dateLabel: match.dateLabel, time: match.time })
      else {
        const suggestion = slots[0]?.times.slice(0, 2).join(' hoặc ')
        reply(`Khung bạn yêu cầu chưa có ${selectedCar.name} tại ${selectedShowroom.name}. Lịch gần nhất đang trống là ${suggestion} vào ${slots[0]?.dateLabel}; hãy chọn một ô trên lịch để tôi giữ đúng xe.`)
      }
      return
    }

    if (stage === 'lookup') {
      const hasPhone = /(0|\+84)[0-9\s.-]{8,12}/.test(value)
      reply(hasPhone
        ? 'Tôi đã nhận thông tin tra cứu. Khi API được nối, ViVi sẽ trả về lịch phù hợp để bạn bổ sung hoặc huỷ ngay tại đây.'
        : 'Để tra cứu chính xác, hãy gửi họ tên và số điện thoại đã dùng khi đặt lịch trong cùng một tin nhắn.')
      return
    }

    reply('Bạn hãy dùng lựa chọn đang hiển thị trong cuộc trò chuyện để tôi tiếp tục đúng bước và giữ chính xác mẫu xe.')
  }

  const startLookup = () => {
    // TODO [BACKEND]: POST /api/v1/test-drive/bookings/lookup with customerName
    // and phone (plus OTP/challenge if required), then expose reschedule/cancel only
    // after verification. Lookup responses should mask PII and include allowedActions.
    addMessage('user', 'Tôi muốn tra cứu lịch đã đặt.')
    setStage('lookup')
    reply('Hãy gửi họ tên và số điện thoại đã dùng khi đặt lịch. Tôi sẽ dùng hai thông tin này để tìm lịch và mở các lựa chọn bổ sung hoặc huỷ.')
  }

  const changePerson = (field, value) => {
    setPerson((current) => ({ ...current, [field]: value }))
    setFormErrors((current) => ({ ...current, [field]: '' }))
  }

  const submitPerson = (event) => {
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
    setStage('review')
    setActiveView('ticket')
    addMessage('user', 'Tôi đã hoàn tất thông tin người lái.')
    reply('Phiếu tạm đã xuất hiện bên trái. Hãy kiểm tra tên, xe, showroom và thời gian; nếu đúng, bấm “Xác nhận đặt lịch” ngay tại đây.')
  }

  const submitBooking = () => {
    setSubmitting(true)
    // TODO [BACKEND]: POST /api/v1/test-drive/bookings with recipientType,
    // vehicleId, showroomId, holdId, customer, driver and licenceConsent. Send an
    // Idempotency-Key to prevent duplicate bookings on retry/double click. Response
    // must include bookingCode, status and assignedSalesRepresentative; 409/410 must
    // return the user to live slot selection without losing customer form values.
    const timer = window.setTimeout(() => {
      setSubmitting(false)
      setBookingCode(`VF-${String(Date.now()).slice(-6)}`)
      setStage('success')
      addMessage('assistant', 'Đặt lịch thành công. Tôi đã giữ lại toàn bộ thông tin bên cạnh. Sau này, bạn chỉ cần nhập họ tên và số điện thoại để tra cứu, bổ sung hoặc huỷ lịch.')
    }, 900)
    timersRef.current.push(timer)
  }

  const viewOptions = selectedCar ? [
    { id: 'car', label: 'Đổi mẫu xe', icon: CarProfile },
    ...(nearbyShowrooms.length ? [{ id: 'map', label: 'Showroom', icon: MapPin }] : []),
    ...(selectedShowroom ? [{ id: 'schedule', label: 'Lịch trống', icon: CalendarBlank }] : []),
    ...(stage === 'review' || stage === 'success' ? [{ id: 'ticket', label: 'Phiếu lịch', icon: CheckCircle }] : []),
  ] : []

  const renderWorkspace = () => {
    if (!selectedCar) return null
    if (activeView === 'map') return <ShowroomMap car={selectedCar} showrooms={nearbyShowrooms} selectedId={showroomId} onSelect={chooseShowroom} />
    if (activeView === 'schedule' && selectedShowroom) return <SchedulePanel car={selectedCar} showroom={selectedShowroom} slots={slots} pendingSlot={pendingSlot} onPick={chooseSlot} />
    if (activeView === 'ticket' && selectedShowroom && selectedSlot) return <BookingTicket car={selectedCar} showroom={selectedShowroom} slot={selectedSlot} person={person} recipient={recipient} bookingCode={bookingCode} />
    return <VehiclePanel car={selectedCar} />
  }

  const showVehicleChoices = stage === 'need_car'

  return (
    <main id="main-content" className={`agent-booking-page ${selectedCar ? 'has-workspace' : 'is-agent-only'} ${stage === 'success' ? 'is-success' : ''}`}>
      <header className="booking-topbar booking-topbar--studio">
        <Link to="/"><ArrowLeft size={17} weight="light" /> Trang chủ</Link>
        <Brand />
        {/* TODO [BACKEND/SESSION — P0]: This claim is fully true only after the draft
            API restores recipient, vehicle, address, showroom, hold and stage. At
            present the browser stores only last-viewed vehicle and dismissal flags. */}
        <div><span /> Tiến trình được giữ trên thiết bị</div>
      </header>

      {!recipient && <RecipientModal onSelect={beginConversation} />}

      {stage === 'success' && selectedCar && selectedShowroom && selectedSlot ? (
        <div className="booking-success-layout">
          <div className="booking-success-documents">
            <VehiclePanel car={selectedCar} />
            <BookingTicket car={selectedCar} showroom={selectedShowroom} slot={selectedSlot} person={person} recipient={recipient} bookingCode={bookingCode} compact />
          </div>
          <section className="vivi-studio vivi-studio--success">
            <div className="vivi-studio__head">
              <ViViAvatar />
              <div><strong>ViVi</strong><small><span /> Lịch đã được xác nhận</small></div>
            </div>
            <div className="vivi-success-copy">
              <CheckCircle size={38} weight="light" />
              <p>Đặt lịch thành công</p>
              <h1>Hẹn gặp bạn tại {selectedShowroom.name}.</h1>
              <span>Mã lịch {bookingCode}</span>
              <p>Để tra cứu, bổ sung hoặc huỷ lịch, bạn chỉ cần cung cấp lại họ tên và số điện thoại đã đăng ký.</p>
              <div><button type="button" onClick={startLookup}>Tra cứu lịch này</button><Link to="/">Về trang chủ</Link></div>
            </div>
          </section>
        </div>
      ) : (
        <div className={`booking-studio ${selectedCar ? 'booking-studio--split' : 'booking-studio--agent'}`}>
          {selectedCar && (
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
              {messages.length ? messages.map((message) => <AgentMessage key={message.id} message={message} />) : (
                <div className="vivi-studio__empty"><ViViAvatar /><p>Chọn người lái thử để ViVi bắt đầu.</p></div>
              )}
              {agentTyping && <div className="vivi-typing" aria-label="ViVi đang trả lời"><span /><span /><span /></div>}
            </div>

            <div className="vivi-studio__composer">
              {showVehicleChoices && (
                <div className="agent-vehicle-choices" aria-label="Mẫu xe gợi ý">
                  {featuredChoices.map((car) => (
                    <button type="button" key={car.id} onClick={() => chooseCar(car)}>
                      <VehicleShot car={car} />
                      <span>{car.name}</span>
                    </button>
                  ))}
                  <button type="button" className="agent-vehicle-choices__all" onClick={() => setSwitcherOpen(true)} aria-haspopup="dialog">
                    <CarProfile size={18} weight="light" />
                    <span>Xem tất cả {cars.length} mẫu</span>
                  </button>
                </div>
              )}

              <ContextualChoices
                stage={stage}
                car={selectedCar}
                address={address}
                showrooms={nearbyShowrooms}
                slots={slots}
                onResolveArea={resolveSuggestedArea}
                onShowroom={chooseShowroom}
                onSlot={chooseSlot}
              />

              {(stage === 'need_car' || stage === 'need_address') && (
                <div className="vivi-capabilities">
                  <button type="button" onClick={startLookup}>Tra cứu lịch đã đặt</button>
                  {selectedCar && <button type="button" onClick={() => setSwitcherOpen(true)} aria-haspopup="dialog">Đổi mẫu xe khác</button>}
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
                <form className="vivi-prompt" onSubmit={handlePrompt}>
                  <label htmlFor="vivi-booking-prompt">Nhắn cho ViVi</label>
                  <div>
                    <textarea id="vivi-booking-prompt" rows="2" value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={stage === 'need_address' || stage === 'need_ward' ? 'Ví dụ: Phường Bến Nghé, TP. Hồ Chí Minh' : 'Nhập mẫu xe, địa chỉ, showroom hoặc thời gian…'} onKeyDown={(event) => {
                      if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault()
                        event.currentTarget.form?.requestSubmit()
                      }
                    }} />
                    <button type="submit" aria-label="Gửi tin nhắn"><PaperPlaneTilt size={18} weight="light" /></button>
                  </div>
                  <small>Enter để gửi · Shift + Enter để xuống dòng</small>
                </form>
              )}
            </div>
          </section>
        </div>
      )}

      {switcherOpen && (
        <VehicleSwitcher
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
    </main>
  )
}
