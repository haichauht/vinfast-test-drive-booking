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
import { useVehicleCatalog } from '../hooks/useSiteData'
import vinfastLogo from '../assets/vinfast-logo.png'
import {
  confirmHeldBooking,
  cancelVerifiedBooking,
  confirmVerifiedReschedule,
  holdBookingSlot,
  holdVerifiedReschedule,
  getVerifiedBooking,
  requestBookingAccess,
  saveBookingCustomer,
  sendBookingMessage,
  searchBookingOptions,
  updateVerifiedBooking,
  verifyBookingAccess,
} from '../api/booking'
import { useBackendStatus } from '../context/BackendStatusContext'
import { BookingCustomerForm as CustomerForm } from '../components/booking/BookingCustomerForm'
import { AgentMessage, ContextualChoices, ViViAvatar } from '../components/booking/BookingChatPrimitives'
import { ShowroomMap as BookingShowroomMap } from '../components/booking/ShowroomMap'
import { BookingTicket, SchedulePanel } from '../components/booking/BookingSummary'
import { VehiclePanel, VehicleSwitcher } from '../components/booking/VehicleWorkspace'
import { BookingAccessPanel } from '../components/booking/BookingAccessPanel'
import { CancellationConfirmModal, RescheduleConfirmModal } from '../components/booking/BookingManagementModals'

const driveCars = []

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
            {hasLocation && (
              <em>{String(showroom.distance).replace('.', ',')} km</em>
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
                {hasLocation && selected.distance !== undefined && selected.distance !== null ? ` · Cách bạn ${String(selected.distance).replace('.', ',')} km` : ''}
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
  const getCar = (id) => cars.find((car) => car.id === id)
  const featuredChoices = ['vf3', 'vf5', 'vf6', 'vf7'].map(getCar).filter(Boolean)
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
  const [locationSuggestions, setLocationSuggestions] = useState([])
  const [nearbyShowrooms, setNearbyShowrooms] = useState([])
  const [showroomId, setShowroomId] = useState('')
  const [pendingSlot, setPendingSlot] = useState(null)
  const [selectedSlot, setSelectedSlot] = useState(null)
  const [confirmSlotOpen, setConfirmSlotOpen] = useState(false)
  const [switcherOpen, setSwitcherOpen] = useState(false)
  const [workspaceHidden, setWorkspaceHidden] = useState(false)
  const [person, setPerson] = useState({ bookingName: '', driverName: '', phone: '', email: '', hasLicense: false, marketingConsent: true })
  const [formErrors, setFormErrors] = useState({})
  const [bookingCode, setBookingCode] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [accessFlow, setAccessFlow] = useState(null)
  const [accessValue, setAccessValue] = useState({ bookingCode: '', phone: '', otpCode: '' })
  const [accessError, setAccessError] = useState('')
  const [accessBusy, setAccessBusy] = useState(false)
  const [accessSecondsLeft, setAccessSecondsLeft] = useState(0)
  const [resendSecondsLeft, setResendSecondsLeft] = useState(0)
  const [accessProfile, setAccessProfile] = useState(null)
  const [rescheduleState, setRescheduleState] = useState(null)
  const [rescheduleSecondsLeft, setRescheduleSecondsLeft] = useState(0)
  const [slots, setSlots] = useState([])
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

  const selectedCar = getCar(selectedCarId)
  // TODO [BACKEND]: Resolve these from fetched state/query caches. A production slot
  // must include inventorySlotId; the UI's date/time tuple is display-only.
  const selectedShowroom = nearbyShowrooms.find((showroom) => showroom.id === showroomId)

  const mapShowrooms = (items, vehicleId = selectedCarId) => items.map((item, index) => ({
    ...item,
    distance: item.distance_km ?? 0,
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
    groups[value].times.push({ time, slotId: item.id })
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

  const showVehiclePanel = (car) => {
    if (!car) return
    setSelectedCarId(car.id)
    setWorkspaceHidden(false)
    setActiveView('car')
    window.sessionStorage.setItem('vinfast:last-viewed-car', car.id)
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
          setBackendError(error.message)
          addMessage('assistant', `Có lỗi xảy ra khi truy vấn dữ liệu showroom: ${error.message}`)
        }
      },
      (error) => {
        setAgentTyping(false)
        console.error("Lỗi lấy vị trí: ", error)
        setBackendError("Không thể truy cập vị trí. Vui lòng bật định vị hoặc nhập địa chỉ thủ công.")
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
        window.sessionStorage.setItem('vinfast:last-viewed-car', agentCar.id)
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
      setBackendError(error.message)
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
    window.sessionStorage.setItem('vinfast:last-viewed-car', car.id)
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
    window.sessionStorage.setItem('vinfast:last-viewed-car', car.id)
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
    // TODO [BACKEND]: Persist showroomId on the draft, then fetch live slots for
    // showroomId + vehicleId. If availability changed, remain on choose_showroom and
    // refresh the cards/map instead of advancing to a blank schedule.
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
      setBackendError(error.message)
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
      const uiActionId = holdActionIdsRef.current.get(actionKey) || `hold:${crypto.randomUUID()}`
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
      setBackendError(error.message)
      reply(`Không thể giữ khung giờ: ${error.message}`)
    }
  }

  const handlePrompt = async (event) => {
    event.preventDefault()
    const value = draft.trim()
    if (!value) return
    setDraft('')
    addMessage('user', value)
    setBackendError('')

    // Keep the visual model panel deterministic even when the LLM responds before
    // a tool result reaches the browser. This mirrors clicking a vehicle suggestion.
    const mentionedCar = resolveAgentCar(value)
    if (mentionedCar) showVehiclePanel(mentionedCar)

    setAgentTyping(true)
    try {
      const result = await sendBookingMessage(value, {
        stage,
        recipient,
        selectedVehicle: selectedCar ? { id: selectedCar.id, name: selectedCar.name } : null,
        selectedShowroom: selectedShowroom ? { id: selectedShowroom.id, name: selectedShowroom.name } : null,
        selectedSlot,
        bookingId: bookingId || null,
        channel: 'booking',
      })
      applyAgentToolResult(result)
      addMessage('assistant', result.response)
      if (/(?:hủy|huy|xóa|xoa)\s*(?:lịch|booking)?/i.test(value)) {
        setStage('lookup')
        setAccessError('')
        setAccessProfile(null)
        setAccessFlow({ phase: 'request', purpose: 'cancel', challengeId: '', expiresAt: 0 })
      }
      if (/(?:đổi|doi)\s*(?:xe|mẫu xe|giờ|gio|thời gian|lịch)/i.test(value)) {
        setStage('lookup')
        setAccessError('')
        setAccessProfile(null)
        setAccessFlow({ phase: 'request', purpose: 'reschedule', challengeId: '', expiresAt: 0 })
      }
    } catch (error) {
      setBackendError(error.message)
      addMessage('assistant', `Không thể kết nối ViVi: ${error.message}`)
    } finally {
      setAgentTyping(false)
    }
  }

  const startLookup = () => {
    // TODO [BACKEND]: POST /api/v1/test-drive/bookings/lookup with customerName
    // and phone (plus OTP/challenge if required), then expose reschedule/cancel only
    // after verification. Lookup responses should mask PII and include allowedActions.
    addMessage('user', 'Tôi muốn tra cứu lịch đã đặt.')
    setStage('lookup')
    setAccessError('')
    // A lookup/edit session also needs reschedule permission for the calendar
    // icon. The backend grants update_details as part of this purpose.
    setAccessFlow({ phase: 'request', purpose: 'reschedule', challengeId: '', expiresAt: 0 })
    reply('Để bảo vệ lịch của bạn, hãy nhập mã lịch và số điện thoại. Tôi sẽ gửi OTP qua Zalo đã liên kết.')
  }

  const changeAccessValue = (field, value) => setAccessValue((current) => ({ ...current, [field]: value }))

  const requestAccessOtp = async (event) => {
    event?.preventDefault()
    setAccessBusy(true); setAccessError('')
    try {
      const result = await requestBookingAccess({ bookingCode: accessValue.bookingCode.trim(), phone: accessValue.phone.trim(), purpose: accessFlow?.purpose || 'update_details' })
      const expiresAt = new Date(result.expires_at).getTime()
      setAccessFlow((current) => ({ phase: 'verify', purpose: current?.purpose || 'update_details', challengeId: result.challenge_id, expiresAt }))
      setAccessValue((current) => ({ ...current, otpCode: '' }))
      setAccessSecondsLeft(Math.max(0, Math.ceil((expiresAt - Date.now()) / 1000)))
      setResendSecondsLeft(result.retry_after_seconds || 60)
      addMessage('assistant', 'Tôi đã gửi mã OTP qua Zalo. Bạn vui lòng nhập mã để tiếp tục.')
    } catch (error) {
      if (error.code === 'OTP_RATE_LIMITED') {
        const seconds = Number(error.message.match(/\d+/)?.[0] || 0)
        setResendSecondsLeft(seconds)
      }
      setAccessError(error.message)
    } finally { setAccessBusy(false) }
  }

  const verifyAccessOtp = async () => {
    if (!accessFlow?.challengeId) return
    setAccessBusy(true); setAccessError('')
    try {
      const verified = await verifyBookingAccess({ challengeId: accessFlow.challengeId, otpCode: accessValue.otpCode })
      const booking = await getVerifiedBooking({ accessToken: verified.access_session_token, bookingId: verified.booking_id })
      setAccessProfile({
        accessToken: verified.access_session_token,
        bookingId: booking.id,
        bookingCode: booking.booking_code || '',
        bookerName: booking.booker?.full_name || '',
        driverName: booking.driver?.full_name || '',
        phone: booking.driver?.phone || booking.booker?.phone || '',
        email: booking.driver?.email || booking.booker?.email || '',
        vehicleName: booking.vehicle?.name || '',
        showroomName: booking.showroom?.name || '',
        showroomId: booking.showroom?.id || '',
        slotTime: booking.slot_time || '',
        slotDate: booking.slot_date || '',
      })
      const isCancellation = accessFlow?.purpose === 'cancel'
      setAccessFlow({ phase: isCancellation ? 'confirm_cancel' : 'edit', purpose: accessFlow?.purpose, challengeId: '', expiresAt: 0 })
      addMessage('assistant', isCancellation ? 'Xác thực thành công. Vui lòng kiểm tra phiếu bên dưới và xác nhận nếu bạn muốn hủy lịch.' : 'Xác thực thành công. Bạn có thể cập nhật thông tin lịch đã đặt bên dưới.')
    } catch (error) { setAccessError(error.message) } finally { setAccessBusy(false) }
  }

  const cancelAccessOtp = () => {
    setAccessFlow(null); setAccessError(''); setAccessSecondsLeft(0); setResendSecondsLeft(0)
    addMessage('assistant', 'Tôi đã dừng bước xác thực. Khi cần xem hoặc chỉnh sửa lịch, bạn có thể yêu cầu lại bất cứ lúc nào.')
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
        driverPatch: accessProfile.driverName.trim() === accessProfile.bookerName.trim() ? null : { full_name: accessProfile.driverName, phone: accessProfile.phone, email: accessProfile.email },
        driverSameAsBooker: accessProfile.driverName.trim() === accessProfile.bookerName.trim(),
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
      if (slots.length) setRescheduleState({ step: 'schedule', car, showroom, slots })
      else {
        const alternatives = await searchBookingOptions({ vehicleModel: car.name })
        setRescheduleState({ step: 'showroom', car, showrooms: alternatives.showrooms || [] })
      }
    } catch (error) { setAccessError(error.message) } finally { setAccessBusy(false) }
  }
  const beginTimeReschedule = () => {
    const car = cars.find((item) => item.name === accessProfile?.vehicleName)
    if (car && accessProfile?.showroomId) {
      setSelectedCarId(car.id)
      setStage('lookup')
      setWorkspaceHidden(false)
      setActiveView('schedule')
      loadRescheduleSlots(car, { id: accessProfile.showroomId, name: accessProfile.showroomName })
    } else setAccessError('Không xác định được mẫu xe hoặc showroom của lịch này.')
  }
  const holdReschedule = async (slot) => {
    setAccessBusy(true); setAccessError('')
    try {
      const held = await holdVerifiedReschedule({ bookingId: accessProfile.bookingId, slotId: slot.id, accessToken: accessProfile.accessToken })
      const startsAt = new Date(slot.start_at)
      setAccessProfile((current) => ({ ...current, slotTime: startsAt.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', hour12: false }), slotDate: new Intl.DateTimeFormat('vi-VN', { weekday: 'long', day: '2-digit', month: '2-digit' }).format(startsAt) }))
      setRescheduleState((current) => ({ ...current, step: 'pending', slot, newBookingId: held.booking_id }))
      setRescheduleSecondsLeft(Math.max(0, Math.ceil((new Date(held.hold_expires_at).getTime() - Date.now()) / 1000)))
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
    if (!rescheduleState || rescheduleSecondsLeft <= 0) return undefined
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
      setBackendError(error.message)
    }
  }

  const submitBooking = async () => {
    setSubmitting(true)
    // TODO [BACKEND]: POST /api/v1/test-drive/bookings with recipientType,
    // vehicleId, showroomId, holdId, customer, driver and licenceConsent. Send an
    // Idempotency-Key to prevent duplicate bookings on retry/double click. Response
    // must include bookingCode, status and assignedSalesRepresentative; 409/410 must
    // return the user to live slot selection without losing customer form values.
    try {
      const actionKey = `${bookingId}:${bookingVersion}`
      const uiActionId = confirmActionIdsRef.current.get(actionKey) || `confirm:${crypto.randomUUID()}`
      confirmActionIdsRef.current.set(actionKey, uiActionId)
      const confirmed = await confirmHeldBooking({ bookingId, version: bookingVersion, uiActionId })
      confirmActionIdsRef.current.delete(actionKey)
      setSubmitting(false)
      setBookingCode(confirmed.booking_code)
      setStage('success')
      addMessage('assistant', 'Đặt lịch thành công. Tôi đã giữ lại toàn bộ thông tin bên cạnh. Sau này, bạn chỉ cần nhập họ tên và số điện thoại để tra cứu, bổ sung hoặc huỷ lịch.')
    } catch (error) {
      setSubmitting(false)
      setBackendError(error.message)
    }
  }

  const viewOptions = selectedCar ? [
    { id: 'car', label: 'Đổi mẫu xe', icon: CarProfile },
    ...(nearbyShowrooms.length ? [{ id: 'map', label: 'Showroom', icon: MapPin }] : []),
    ...(selectedShowroom ? [{ id: 'schedule', label: 'Lịch trống', icon: CalendarBlank }] : []),
    ...(stage === 'review' || stage === 'success' ? [{ id: 'ticket', label: 'Phiếu lịch', icon: CheckCircle }] : []),
  ] : []

  const renderWorkspace = () => {
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
    <main id="main-content" className={`agent-booking-page ${selectedCar && !workspaceHidden ? 'has-workspace' : 'is-agent-only'} ${stage === 'success' ? 'is-success' : ''}`}>
      <header className="booking-topbar booking-topbar--studio">
        <Link to="/"><ArrowLeft size={17} weight="light" /> Trang chủ</Link>
        <Brand />
        {/* TODO [BACKEND/SESSION — P0]: This claim is fully true only after the draft
            API restores recipient, vehicle, address, showroom, hold and stage. At
            present the browser stores only last-viewed vehicle and dismissal flags. */}
        <div><span /> Tiến trình được giữ trên thiết bị</div>
      </header>

      {selectedCar && workspaceHidden && (
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
        <div className={`booking-studio ${selectedCar && !workspaceHidden ? 'booking-studio--split' : 'booking-studio--agent'}`}>
          {selectedCar && !workspaceHidden && (
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
              {messages.length ? messages.map((message) => <AgentMessage key={message.id} message={message} />) : (
                <div className="vivi-studio__empty"><ViViAvatar /><p>Chọn người lái thử để ViVi bắt đầu.</p></div>
              )}
              {agentTyping && (
                <div className="vivi-message vivi-message--assistant">
                  <ViViAvatar compact />
                  <div className="vivi-typing" aria-label="ViVi đang trả lời">
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              )}
            </div>

            <div className="vivi-studio__composer">
              {backendError && <p className="booking-api-error" role="alert">{backendError}</p>}
              {accessFlow && accessFlow.phase !== 'confirm_cancel' ? (
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
                  onRescheduleTime={beginTimeReschedule}
                  rescheduleSecondsLeft={rescheduleSecondsLeft}
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
