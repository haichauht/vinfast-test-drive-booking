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
import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  ArrowsClockwise,
  CalendarBlank,
  CarProfile,
  CaretDown,
  CaretLeft,
  Check,
  CheckCircle,
  Clock,
  Crosshair,
  MagnifyingGlass,
  MapPin,
  Minus,
  NavigationArrow,
  PaperPlaneTilt,
  PencilSimple,
  Prohibit,
  Plus,
  ShieldCheck,
  User,
  UserPlus,
  X,
} from '@phosphor-icons/react'
import { Brand } from '../components/Brand'
import { SmartImage } from '../components/SmartImage'
import { carGroups } from '../data/cars'
import { useBookingUpsell, useVehicleCatalog } from '../hooks/useSiteData'
import { BookingUpsell } from '../components/booking/BookingUpsell'
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
  resetBookingConversation,
  saveBookingCustomer,
  sendDriverChatMessage,
  sendBookingMessage,
  searchBookingOptions,
  updateVerifiedBooking,
  verifyBookingAccess,
} from '../api/booking'
import {
  BookingMode,
  InteractionEvent,
  bookingInteractionReducer,
  createInteractionState,
  selectAllowedActions,
  selectComposerMode,
  selectWorkspace,
  serializeInteractionState,
  toLegacyStage,
} from '../state/bookingInteraction'
import { CHAT_MESSAGE_MAX_LENGTH } from '../api/contracts'
import { actionId } from '../api/ids'
import { useBackendStatus } from '../context/BackendStatusContext'
import { BookingCustomerForm as CustomerForm } from '../components/booking/BookingCustomerForm'
import { ShowroomMap as BookingShowroomMap } from '../components/booking/ShowroomMap'
import { BookingNextSteps, BookingTicket, SchedulePanel, buildGoogleCalendarUrl } from '../components/booking/BookingSummary'
import { BookingAccessPanel } from '../components/booking/BookingAccessPanel'
import { CancellationConfirmModal, RescheduleConfirmModal } from '../components/booking/BookingManagementModals'
import { BookingSuccessVehicleModel, preloadVehicle3dRuntime } from '../components/Vehicle3DExperience'
import { BookingSuccessCinematic } from '../components/BookingSuccessCinematic'
import { getVehicle3dModel } from '../data/vehicle3d'
import { RecipientModal, ResumeModal } from '../components/booking/BookingModalPrimitives'
import { AgentMessage, ViviStatusTyping, ViViAvatar, ContextualChoices } from '../components/booking/BookingChatPrimitives'
import { VehicleShot, VehicleSwitcher, VehiclePanel } from '../components/booking/VehicleWorkspace'
import { BookingHeader } from '../components/booking/BookingHeader'

const vinfastLogo = commonMedia.vinfastLogo
const driveCars = []
const BOOKING_UI_STATE_KEY = 'vinfast:booking-ui-state'
const DRIVER_INVITATION_HISTORY_KEY = 'vinfastDriverInvitationToken'
const DRIVER_GREETING = 'ViVi sẽ đồng hành cùng bạn chuẩn bị cho buổi lái thử. ViVi có thể giúp chọn những điều nên thử trên xe, các câu hỏi nên trao đổi với tư vấn viên và checklist trước giờ hẹn. Chia sẻ tình huống sử dụng xe chính—đi làm, chở gia đình hay đi xa—để ViVi ưu tiên các bài test sát nhu cầu.'

const takeDriverInvitationToken = () => {
  const params = new URLSearchParams(window.location.hash.replace(/^#/, ''))
  const token = params.get('driver-invitation') || ''
  const state = window.history.state && typeof window.history.state === 'object'
    ? window.history.state
    : {}
  if (!token) return typeof state[DRIVER_INVITATION_HISTORY_KEY] === 'string'
    ? state[DRIVER_INVITATION_HISTORY_KEY]
    : ''
  params.delete('driver-invitation')
  const hash = params.toString()
  window.history.replaceState(
    { ...state, [DRIVER_INVITATION_HISTORY_KEY]: token },
    '',
    `${window.location.pathname}${window.location.search}${hash ? `#${hash}` : ''}`,
  )
  return token
}

// Dùng chung cho cả người đặt lẫn người lái — hai đầu mối phải được kiểm cùng một chuẩn.
const PHONE_PATTERN = /^(0|\+84)[0-9\s.-]{8,12}$/
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/**
 * Đổi lỗi của bước xin OTP thành câu người dùng hiểu và làm được gì đó.
 *
 * Vì sao cần: khi kênh gửi OTP chưa được cấu hình đúng, backend ném 500 và `apiPost`
 * chỉ còn câu mặc định "Yêu cầu không thành công." — người dùng không biết chuyện gì
 * xảy ra, cũng không biết nên làm gì tiếp.
 *
 * TODO [BACKEND/OTP]: 500 nên đổi thành lỗi có mã (vd OTP_CHANNEL_UNAVAILABLE) để
 * frontend phân biệt được "cấu hình sai" với "mạng lỗi".
 */
/**
 * Tạo file .ics cho buổi lái thử và tải xuống.
 *
 * Vì sao có: no-show là vấn đề lõi của dự án (nghiên cứu người dùng: một người tham gia
 * đã bỏ hẹn thật). Cho người dùng đưa buổi hẹn thẳng vào lịch điện thoại là cách chống
 * quên rẻ nhất, và làm được HOÀN TOÀN ở frontend — không phụ thuộc email/OTP đang hỏng.
 *
 * Chỉ ghi dữ liệu có thật: giờ bắt đầu/kết thúc từ slot, tên + địa chỉ showroom, mã lịch.
 * Không có giờ kết thúc thì mặc định 60 phút và ghi rõ trong mô tả là ước tính.
 */
const escapeIcs = (value = '') => String(value)
  .replace(/\\/g, '\\\\')
  .replace(/;/g, '\\;')
  .replace(/,/g, '\\,')
  .replace(/\r?\n/g, '\\n')

const downloadCalendarInvite = ({ car, showroom, slot, bookingCode }) => {
  let start = null
  let end = null

  if (slot?.startAt) {
    start = new Date(slot.startAt)
    end = slot.endAt ? new Date(slot.endAt) : new Date(start.getTime() + 45 * 60000)
  } else if (slot?.date && slot?.time) {
    const timeClean = slot.time.length === 5 ? slot.time : slot.time.padStart(5, '0')
    const dateStr = `${slot.date}T${timeClean}:00+07:00`
    start = new Date(dateStr)
    end = new Date(start.getTime() + 45 * 60000)
  }

  if (!start || isNaN(start.getTime())) return false
  const stamp = (date) => date.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')

  const description = [
    `Mã lịch: ${bookingCode || 'Tạm giữ'}`,
    'Mang theo giấy phép lái xe còn hiệu lực.',
    showroom?.phone ? `Showroom: ${showroom.phone}` : '',
    !slot?.endAt ? '(Thời lượng ước tính: 45 phút, showroom sẽ đón tiếp trực tiếp.)' : '',
  ].filter(Boolean).join('\n')

  const ics = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//VinFast//Test Drive//VI',
    'BEGIN:VEVENT',
    `UID:${bookingCode || 'booking'}-${Date.now()}@vinfast`,
    `DTSTAMP:${stamp(new Date())}`,
    `DTSTART:${stamp(start)}`,
    `DTEND:${stamp(end)}`,
    `SUMMARY:${escapeIcs(`Lái thử ${car?.name || 'VinFast'} · ${bookingCode || 'Lịch hẹn'}`)}`,
    `LOCATION:${escapeIcs([showroom?.name, showroom?.address].filter(Boolean).join(', '))}`,
    `DESCRIPTION:${escapeIcs(description)}`,
    'BEGIN:VALARM',
    'TRIGGER:-PT2H',
    'ACTION:DISPLAY',
    'DESCRIPTION:Buổi lái thử VinFast sắp bắt đầu',
    'END:VALARM',
    'END:VEVENT',
    'END:VCALENDAR',
  ].join('\r\n')

  const url = URL.createObjectURL(new Blob([ics], { type: 'text/calendar;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = `lai-thu-${bookingCode || 'vinfast'}.ics`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
  return true
}

const accessErrorMessage = (error) => {
  if (error?.code === 'ZALO_NOT_LINKED') {
    return 'Số điện thoại này chưa liên kết với Zalo Bot của VinFast nên bạn chưa nhận được mã.'
  }
  if (error?.code === 'BOOKING_NOT_FOUND' || error?.status === 404) {
    return 'ViVi không tìm thấy lịch nào ứng với thông tin này. Bạn kiểm tra lại email đã dùng khi đặt lịch giúp ViVi nhé.'
  }
  if (error?.status >= 500 || !error?.code) {
    return 'ViVi chưa gửi được mã xác thực cho bạn lúc này. Bạn thử lại sau ít phút, hoặc gọi hotline 1900 23 23 89 để được hỗ trợ trực tiếp.'
  }
  return error.message
}
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

export function BookingPage() {
  const { bookingStatus, retry } = useBackendStatus()
  // UX state machine (server should return/validate the same nextStage values):
  // idle -> need_car -> need_address -> need_ward -> choose_showroom ->
  // choose_slot -> collect_info -> review -> success. `lookup` is a side flow.
  // The browser may render optimistically, but inventory holds and terminal booking
  // state are always server-authoritative. Full transition table: BACKEND_HANDOFF.md.
  const [searchParams] = useSearchParams()
  const [driverInvitationToken] = useState(takeDriverInvitationToken)
  const isDriverChat = Boolean(driverInvitationToken)
  const { cars } = useVehicleCatalog()
  const [restoredUi] = useState(readBookingUiState)
  const getCar = (id) => cars.find((car) => car.id === id)
  // 3 mẫu upsell do sale admin chọn bên trang quản trị. Không hard-code danh sách xe ở đây
  // nữa: đổi mẫu muốn đẩy là việc của người bán hàng, không phải việc phải sửa code và deploy.
  const upsell = useBookingUpsell()
  const upsellCars = upsell.vehicleIds.map(getCar).filter(Boolean)
  const routeCar = getCar(searchParams.get('car'))
  const initialCar = routeCar || null
  const shouldOfferResume = !isDriverChat && Boolean(
    !initialCar && (
      (restoredUi.stage && restoredUi.stage !== 'idle') ||
      (restoredUi.interaction?.phase && restoredUi.interaction.phase !== 'idle') ||
      (Array.isArray(restoredUi.messages) && restoredUi.messages.length)
    ),
  )
  const restoredLastConfirmed = useMemo(() => {
    try {
      const storedStr = window.sessionStorage.getItem('LAST_CONFIRMED_BOOKING')
      return storedStr ? JSON.parse(storedStr) : null
    } catch {
      return null
    }
  }, [])

  const [recipient, setRecipient] = useState(isDriverChat ? 'driver' : (initialCar ? '' : restoredUi.recipient || ''))
  const [resumePending, setResumePending] = useState(() => Boolean(
    shouldOfferResume,
  ))
  const [selectedCarId, setSelectedCarId] = useState(initialCar?.id || restoredUi.selectedCarId || restoredLastConfirmed?.car?.id || '')
  const [interaction, dispatchInteraction] = useReducer(
    bookingInteractionReducer,
    {
      stage: isDriverChat ? 'idle' : (shouldOfferResume ? restoredUi.stage || 'idle' : initialCar ? 'need_address' : 'idle'),
      activeView: isDriverChat ? 'agent' : (initialCar ? 'car' : restoredUi.activeView || 'agent'),
      interaction: shouldOfferResume ? restoredUi.interaction : null,
    },
    createInteractionState,
  )
  const stage = toLegacyStage(interaction)
  const activeView = interaction.activeView
  const setStage = useCallback((nextStage) => {
    dispatchInteraction({ type: InteractionEvent.SET_PHASE, stage: nextStage })
  }, [])
  const setActiveView = useCallback((nextView) => {
    dispatchInteraction({ type: InteractionEvent.SET_ACTIVE_VIEW, activeView: nextView })
  }, [])
  const [messages, setMessages] = useState(isDriverChat
    ? [{ id: 'driver-invitation-greeting', role: 'assistant', text: DRIVER_GREETING }]
    : (shouldOfferResume && Array.isArray(restoredUi.messages) ? restoredUi.messages : []))
  const [draft, setDraft] = useState('')
  const [agentTyping, setAgentTyping] = useState(false)
  const [checkingVehicleName, setCheckingVehicleName] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [address, setAddress] = useState(restoredUi.address || { province: '', detail: '' })
  const [locationSuggestions, setLocationSuggestions] = useState([])
  const [nearbyShowrooms, setNearbyShowrooms] = useState(
    Array.isArray(restoredUi.nearbyShowrooms) && restoredUi.nearbyShowrooms.length
      ? restoredUi.nearbyShowrooms
      : restoredLastConfirmed?.showroom ? [restoredLastConfirmed.showroom] : []
  )
  const [showroomId, setShowroomId] = useState(restoredUi.showroomId || restoredLastConfirmed?.showroom?.id || '')
  const [pendingSlot, setPendingSlot] = useState(null)
  const [selectedSlot, setSelectedSlot] = useState(restoredLastConfirmed?.slot || null)
  const [confirmSlotOpen, setConfirmSlotOpen] = useState(false)
  const [switcherOpen, setSwitcherOpen] = useState(false)
  const [workspaceHidden, setWorkspaceHidden] = useState(false)
  const [person, setPerson] = useState(restoredLastConfirmed?.person || {
    bookingName: '',
    driverName: '',
    phone: '',
    email: '',
    driverSameContact: true,
    driverPhone: '',
    driverEmail: '',
    hasLicense: false,
    marketingConsent: true,
  })
  const [formErrors, setFormErrors] = useState({})
  const [bookingCode, setBookingCode] = useState(restoredLastConfirmed?.bookingCode || '')
  const [bookingAdvisor, setBookingAdvisor] = useState(restoredLastConfirmed?.advisor || null)
  const [submitting, setSubmitting] = useState(false)
  const [successCinematic, setSuccessCinematic] = useState(false)
  const [accessFlow, setAccessFlow] = useState(null)
  const [accessValue, setAccessValue] = useState({ bookingCode: '', email: '', otpCode: '' })
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
  const [userLocation, setUserLocation] = useState(restoredUi.userLocation || null)
  const messagesRef = useRef(null)
  const timersRef = useRef([])
  const holdActionIdsRef = useRef(new Map())
  // Đếm lượt tìm khung giờ. Bấm showroom A rồi bấm nhanh sang B sẽ có 2 request cùng bay;
  // ai về sau thắng, nên nếu không đánh số thì slot của A có thể đắp lên tên showroom B.
  const showroomRequestRef = useRef(0)
  const confirmActionIdsRef = useRef(new Map())
  const holdExpiredRef = useRef(false)
  const otpChallengeIdRef = useRef('')
  const otpCodeRef = useRef('')
  const sendingRef = useRef(false)
  const driverConversationIdRef = useRef('')

  const [inlineOtpDigits, setInlineOtpDigits] = useState(['', '', '', '', '', ''])
  const [inlineOtpError, setInlineOtpError] = useState('')
  const [inlineOtpBusy, setInlineOtpBusy] = useState(false)
  const [inlineOtpMock, setInlineOtpMock] = useState('')
  const [inlineOtpChallengeId, setInlineOtpChallengeId] = useState('')

  const selectedCar = getCar(selectedCarId)
  // ĐÃ XONG: showroom và khung giờ lấy thật từ backend qua searchBookingOptions().
  // Mỗi slot đã mang id thật của backend; cặp ngày/giờ trong UI chỉ để hiển thị.
  const selectedShowroom = nearbyShowrooms.find((showroom) => showroom.id === showroomId)
  const composerDisabled = isSending || agentTyping
  const allowedActions = useMemo(() => (isDriverChat ? [] : selectAllowedActions(interaction, {
    allowedBookingActions: accessProfile?.allowedActions || [],
  })), [interaction, accessProfile?.allowedActions, isDriverChat])
  const workspaceModel = useMemo(() => selectWorkspace(interaction), [interaction])
  const composerMode = useMemo(() => selectComposerMode(interaction), [interaction])
  const hasWorkspaceContent = Boolean(selectedCar || accessProfile)
  const workspaceVisible = workspaceModel.visible && hasWorkspaceContent && !workspaceHidden

  /**
   * Kết thúc cinematic → quay về khung chat, KHÔNG chuyển sang trang tĩnh.
   *
   * ViVi chủ động mở lời thay vì để người dùng nhìn một bảng thông tin câm:
   * gọi tên người đặt, nói còn bao nhiêu ngày nữa, và nói rõ mình vẫn ở đây.
   * Số ngày tính từ `slot.startAt` (mốc ISO thật), không đoán từ chuỗi hiển thị.
   */
  // BookingSuccessCinematic đưa `onComplete` vào dependencies của timeline GSAP, nên hàm này
  // PHẢI giữ nguyên identity — đổi một cái là cinematic chạy lại từ đầu. Giữ logic trong ref
  // để vẫn đọc được giá trị mới nhất mà vỏ ngoài không bao giờ đổi.
  const completeSuccessRef = useRef(() => {})
  completeSuccessRef.current = () => {
    setSuccessCinematic(false)
    setStage('success')
    setActiveView('ticket')

    const rawName = (person.bookingName || person.driverName || '').trim().split(/\s+/).pop() || ''
    const firstName = rawName ? rawName.charAt(0).toUpperCase() + rawName.slice(1) : ''
    const greeting = firstName ? `${firstName} ơi, ` : ''

    setMessages((current) => [
      ...current,
      {
        id: `${Date.now()}-${current.length}`,
        role: 'assistant',
        text: `${greeting}ViVi và showroom đều đã nhận được lịch đặt lái thử của bạn.`,
        emphasis: true,
      },
      {
        id: `${Date.now()}-${current.length + 1}`,
        role: 'assistant',
        text: DRIVER_GREETING,
      },
      {
        id: `${Date.now()}-${current.length + 2}-next-steps`,
        role: 'assistant',
        type: 'next_steps',
        text: '',
      },
    ])
  }
  const completeBookingSuccess = useCallback(() => completeSuccessRef.current(), [])

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
    if (isDriverChat) return
    const safeMessages = messages
      .filter((message) => !isSensitiveChatText(message.text || ''))
      .map(({ id, role, text, type, emphasis }) => ({ id, role, text, type, emphasis }))
      .slice(-30)
    window.sessionStorage.setItem(BOOKING_UI_STATE_KEY, JSON.stringify({
      recipient,
      selectedCarId,
      showroomId,
      nearbyShowrooms,
      slots,
      address,
      userLocation,
      messages: safeMessages,
      interaction: serializeInteractionState(interaction),
    }))
  }, [recipient, selectedCarId, showroomId, nearbyShowrooms, slots, address, userLocation, messages, interaction, isDriverChat])

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
    // Giữ luôn giờ kết thúc: màn hướng dẫn sau đặt lịch cần nói thời lượng buổi lái thử,
    // mà backend chỉ trả start_at/end_at ở đây — bỏ end_at đi là mất căn cứ, phải đoán.
    const end = item.end_at ? new Date(item.end_at) : null
    groups[value].times.push({
      time,
      endTime: end ? end.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', hour12: false }) : '',
      durationMinutes: end ? Math.max(0, Math.round((end - start) / 60000)) : 0,
      // Mốc ISO gốc: cần cho việc đếm số ngày còn lại và tạo file lịch (.ics).
      // Chuỗi hiển thị "17:30 · Th 4, 19/08" không parse ngược lại được cho chắc.
      startAt: item.start_at,
      endAt: item.end_at || '',
      slotId: item.id,
      isAvailable: item.status === 'available',
      unavailableLabel: item.status === 'held' ? 'Đang được giữ' : 'Đã có lịch',
    })
    return groups
  }, {}))

  const formatBookingSummary = (booking, index = 0) => {
    const startsAt = booking.start_at ? new Date(booking.start_at) : null
    const displayTime = startsAt && !Number.isNaN(startsAt.getTime())
      ? new Intl.DateTimeFormat('vi-VN', { weekday: 'long', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }).format(startsAt)
      : 'Lịch lái thử'
    return {
      ...booking,
      display_time: displayTime,
      display_label: `${index + 1}. ${booking.booking_code || 'Lịch lái thử'} - ${displayTime}${booking.vehicle_name ? ` - ${booking.vehicle_name}` : ''}${booking.showroom_name ? ` tại ${booking.showroom_name}` : ''}`,
    }
  }

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

  const requestUserLocation = ({ addUserMessage = true } = {}) => {
    if (!navigator.geolocation) {
      setBackendError("Trình duyệt của bạn không hỗ trợ định vị GPS.")
      return
    }
    if (!selectedCar) {
      setStage('need_car')
      setActiveView('car')
      addMessage('assistant', 'Bạn chọn mẫu xe muốn lái thử trước nhé, rồi tôi sẽ xin quyền định vị để tìm showroom gần bạn.')
      return
    }

    setBackendError('')
    if (addUserMessage) addMessage('user', 'Định vị vị trí hiện tại của tôi.')
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
          setShowroomId('')
          setAgentTyping(false)
          if (showrooms.length) {
            setStage('choose_showroom')
            setActiveView('map')
            addMessage('assistant', `ViVi đã định vị vị trí và tìm thấy ${showrooms.length} showroom gần bạn nhất có xe ${selectedCar.name}. Mời bạn chọn showroom hiển thị trên bản đồ để tiếp tục đặt lịch.`)
          } else {
            setStage('need_address')
            addMessage('assistant', `Rất tiếc, ViVi chưa tìm thấy showroom nào gần vị trí của bạn có sẵn xe ${selectedCar.name}. Bạn hãy thử nhập một địa chỉ cụ thể khác ở khung chat bên dưới nhé.`)
          }
        } catch (error) {
          setAgentTyping(false)
          addMessage('assistant', `Có lỗi xảy ra khi truy vấn dữ liệu showroom: ${error.message}`)
        }
      },
      (error) => {
        setAgentTyping(false)
        console.error("Lỗi lấy vị trí: ", error)
        addMessage('assistant', 'ViVi không nhận được phản hồi định vị. Hãy nhắn cho ViVi quận/huyện hoặc tỉnh/thành phố của bạn (ví dụ: "Quận 1, TP HCM") để ViVi tìm showroom nhé!')
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

  const completeOtpChallenge = () => {
    setAccessSecondsLeft(0)
    setResendSecondsLeft(0)
    otpChallengeIdRef.current = ''
    otpCodeRef.current = ''
  }

  const clearManagementContext = ({ resetConversation = true, event = InteractionEvent.EXIT_MANAGE_BOOKING } = {}) => {
    setAccessFlow(null)
    setAccessProfile(null)
    setAccessibleBookings([])
    setExpandedBookingId('')
    setRescheduleState(null)
    setRescheduleSecondsLeft(0)
    setAccessError('')
    setAccessSecondsLeft(0)
    setResendSecondsLeft(0)
    setAccessValue({ bookingCode: '', email: '', otpCode: '' })
    otpChallengeIdRef.current = ''
    otpCodeRef.current = ''
    dispatchInteraction({ type: event })
    if (resetConversation) resetBookingConversation()
  }

  const applyServerUiDirective = (ui) => {
    const phaseEvents = {
      access_request: InteractionEvent.ACCESS_REQUESTED,
      access_verify: InteractionEvent.ACCESS_VERIFY,
      booking_list: InteractionEvent.ACCESS_LIST,
    }
    if (phaseEvents[ui?.phase]) {
      dispatchInteraction({ type: phaseEvents[ui.phase] })
      return
    }
    const legacyStages = {
      choose_showroom: 'choose_showroom',
      choose_slot: 'choose_slot',
      collect_info: 'collect_info',
      review: 'review',
      success: 'success',
    }
    if (legacyStages[ui?.phase]) setStage(legacyStages[ui.phase])
  }

  const findSlotById = (groups, slotId) => {
    if (!slotId) return null
    for (const group of groups) {
      const match = group.times.find((item) => item.slotId === slotId)
      if (match) return { date: group.value, dateLabel: group.dateLabel, ...match }
    }
    return null
  }

  /**
   * Tra ra khung giờ THẬT của một slot vừa được giữ.
   *
   * Vì sao cần: backend trả về khi giữ chỗ chỉ gồm booking_id, status, version,
   * hold_expires_at, remaining_seconds và showroom — KHÔNG có ngày/giờ của slot
   * (backend/src/services/booking/lifecycle.py, hàm hold_slot).
   *
   * Bản trước xử lý thiếu dữ liệu bằng cách ghi cứng `time: '21:00 - 22:00'` rồi mang
   * đúng chuỗi đó ra modal xác nhận, phiếu review và màn thành công — tức là hiển thị
   * một giờ hẹn KHÔNG có thật cho người dùng xác nhận. Nay không bịa nữa: tra trong danh
   * sách đang có, không thấy thì hỏi lại backend đúng showroom đó.
   */
  const resolveHeldSlot = async (slotId, slotShowroomId) => {
    const local = findSlotById(slots, slotId)
    if (local) return local
    if (!selectedCar || !slotShowroomId) return null
    try {
      const refreshed = await searchBookingOptions({
        vehicleModel: selectedCar.name,
        showroomId: slotShowroomId,
      })
      const grouped = groupSlots(refreshed.slots || [])
      setSlots(grouped)
      return findSlotById(grouped, slotId)
    } catch {
      return null
    }
  }

  /**
   * Xoá SẠCH mọi thứ phụ thuộc vào mẫu xe đang chọn.
   *
   * Trước đây ba nhánh đổi xe (chooseCar, switchCar và nhánh `vehicle_info` trong
   * handlePrompt) mỗi nhánh dọn một tập trạng thái khác nhau, và KHÔNG nhánh nào dọn
   * `slots`, `bookingId`, `bookingVersion`, `holdExpiresAt`. Hậu quả đã kiểm chứng:
   * `slots` được ghi vào sessionStorage nên đổi xe rồi tải lại trang là thấy khung giờ
   * của mẫu xe CŨ nằm dưới tên mẫu xe MỚI.
   *
   * TODO [BACKEND/BOOKING]: chưa có API nhả chỗ đang giữ. Đổi xe giữa chừng thì chỗ giữ
   * của mẫu cũ nằm lại tới khi hết hạn (~2 phút), làm khung giờ đó bị khoá oan.
   */
  const resetSelectionForVehicleChange = () => {
    showroomRequestRef.current += 1 // vô hiệu hoá mọi lượt tìm khung giờ đang bay
    setPendingSlot(null)
    setSelectedSlot(null)
    setConfirmSlotOpen(false)
    setNearbyShowrooms([])
    setLocationSuggestions([])
    setShowroomId('')
    setSlots([])
    setAddress({ province: '', detail: '' })
    setBookingId('')
    setBookingVersion(0)
    setHoldExpiresAt(null)
    setTimeLeft('')
    setBackendError('')
  }

  const applyAgentToolResult = async (result) => {
    if (!result || !result.action_data) return false
    applyServerUiDirective(result.ui)
    setWorkspaceHidden(false)

    if (result.tool_name === 'request_user_location' || result.action_data.requires_client_geolocation) {
      requestUserLocation({ addUserMessage: false })
      return false
    }

    if (result.tool_name === 'request_booking_access') {
      const data = result.action_data
      const toolInput = result.tool_input || {}
      const accessPurpose = data.purpose || toolInput.purpose || 'lookup'
      if (data.requires_contact_value) {
        otpChallengeIdRef.current = ''
        otpCodeRef.current = ''
        dispatchInteraction({ type: InteractionEvent.ACCESS_REQUESTED })
        setAccessError('')
        setAccessSecondsLeft(0)
        setResendSecondsLeft(0)
        setAccessValue((current) => ({
          ...current,
          bookingCode: '',
          email: '',
          otpCode: '',
        }))
        setAccessFlow({ phase: 'request', purpose: accessPurpose, challengeId: '', expiresAt: 0 })
        return false
      }
      const expiresAt = data.expires_at ? new Date(data.expires_at).getTime() : 0
      if (!data.challenge_id || !expiresAt || Number.isNaN(expiresAt)) return
      otpChallengeIdRef.current = data.challenge_id
      otpCodeRef.current = ''
      dispatchInteraction({ type: InteractionEvent.ACCESS_VERIFY })
      setAccessError('')
      setAccessValue((current) => ({
        ...current,
        bookingCode: '',
        email: String(toolInput.contact_value || current.email || ''),
        otpCode: '',
      }))
      setAccessFlow({
        phase: 'verify',
        purpose: accessPurpose,
        challengeId: data.challenge_id,
        expiresAt,
      })
      setAccessSecondsLeft(Math.max(0, Math.ceil((expiresAt - Date.now()) / 1000)))
      setResendSecondsLeft(data.retry_after_seconds || 60)
      return false
    }

    if (result.tool_name === 'verify_booking_access') {
      const verified = result.action_data
      completeOtpChallenge()
      const accessPurpose = accessFlow?.purpose || result.tool_input?.purpose || 'lookup'
      const bookings = await listVerifiedBookings({ accessToken: verified.access_session_token })
      const formattedBookings = (bookings.data || bookings || []).map(formatBookingSummary)
      setAccessibleBookings(formattedBookings)
      setActiveView('bookings')
      const isCancellation = accessPurpose === 'cancel'

      if (formattedBookings.length > 1) {
        setAccessProfile({
          accessToken: verified.access_session_token,
          accessPurpose,
          bookingId: verified.booking_id,
          bookingCode: '',
          bookerName: '',
          driverName: '',
          phone: '',
          email: accessValue.email,
          permissions: verified.permissions || [],
          allowedActions: [],
          vehicleName: '',
          vehicleModelId: '',
          showroomName: '',
          showroomId: '',
          showroomAddress: '',
          advisorName: '',
          advisorPhone: '',
          slotTime: '',
          slotDate: '',
        })
        setExpandedBookingId('')
        setAccessFlow(null)
        dispatchInteraction({ type: InteractionEvent.ACCESS_LIST })
        otpChallengeIdRef.current = ''
        otpCodeRef.current = ''
        addMessage('assistant', `Xác thực thành công. ViVi tìm thấy ${formattedBookings.length} lịch hợp lệ với email này, bạn chọn lịch muốn xem hoặc chỉnh sửa nhé.`)
        return true
      }

      if (formattedBookings.length === 0) {
        clearManagementContext({ resetConversation: false })
        addMessage('assistant', 'Bạn đã xác thực thành công, nhưng ViVi chưa tìm thấy lịch nào còn hiệu lực với email này.')
        return true
      }

      const booking = await getVerifiedBooking({ accessToken: verified.access_session_token, bookingId: formattedBookings[0]?.id || verified.booking_id })
      setAccessProfile({
        accessToken: verified.access_session_token,
        accessPurpose,
        bookingId: booking.id,
        bookingCode: booking.booking_code || '',
        bookerName: booking.booker?.full_name || '',
        driverName: booking.driver?.full_name || '',
        phone: booking.driver?.phone || booking.booker?.phone || '',
        email: booking.driver?.email || booking.booker?.email || '',
        permissions: verified.permissions || [],
        allowedActions: booking.allowed_actions || [],
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
      setAccessFlow({ phase: isCancellation ? 'confirm_cancel' : 'edit', purpose: accessPurpose, challengeId: '', expiresAt: 0 })
      dispatchInteraction({
        type: isCancellation ? InteractionEvent.ACCESS_CANCEL_CONFIRM : InteractionEvent.ACCESS_EDIT,
      })
      otpChallengeIdRef.current = ''
      otpCodeRef.current = ''
      addMessage('assistant', isCancellation ? 'Xác thực thành công. Vui lòng kiểm tra phiếu bên dưới và xác nhận nếu bạn muốn hủy lịch.' : 'Bạn đã xác thực thành công. Bạn có thể cập nhật thông tin lịch đã đặt ngay bên dưới.')
      return true
    }

    if (result.tool_name === 'search_test_drive_options') {
      const data = result.action_data
      const toolInput = result.tool_input || {}
      const agentCar = resolveAgentCar(data.resolved_vehicle)
      const vehicleId = agentCar?.id || selectedCarId

      if (agentCar) {
        if (!recipient) setRecipient('self')
        setWorkspaceHidden(false)
        if (interaction.mode === BookingMode.MANAGE_BOOKING) {
          clearManagementContext({ resetConversation: true, event: InteractionEvent.VIEW_VEHICLE })
        } else {
          dispatchInteraction({ type: InteractionEvent.VIEW_VEHICLE })
        }
        setSelectedCarId(agentCar.id)
      }

      if (data.search_stage === 'showroom_selection') {
        const mapped = mapShowrooms(data.showrooms || [], vehicleId)
        const queriedAddress = String(toolInput.address || '').trim()
        setPendingSlot(null)
        setSelectedSlot(null)
        setConfirmSlotOpen(false)
        setShowroomId('')

        if (mapped.length) {
          if (queriedAddress) setAddress({ province: '', detail: queriedAddress })
          setUserLocation(null)
          setLocationSuggestions([])
          setNearbyShowrooms(mapped)
          setStage('choose_showroom')
          const hasLocationInput = Boolean(queriedAddress || toolInput.latitude || toolInput.longitude || toolInput.showroom_query)
          if (hasLocationInput) {
            setActiveView('map')
          } else {
            setActiveView('car')
          }
        } else {
          setAddress({ province: '', detail: queriedAddress })
          setNearbyShowrooms([])
          setLocationSuggestions([])
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

      let slotShowroomId = showroomId
      if (data.showroom) {
        const [mappedShowroom] = mapShowrooms([data.showroom], selectedCarId)
        setNearbyShowrooms((current) => current.some((item) => item.id === mappedShowroom.id) ? current : [...current, mappedShowroom])
        setShowroomId(mappedShowroom.id)
        slotShowroomId = mappedShowroom.id
      }

      const targetSlot = await resolveHeldSlot(toolInput.slot_id, slotShowroomId)

      // Không tra được ngày giờ thật thì KHÔNG mở hộp xác nhận. Bắt người dùng bấm
      // "Xác nhận khung giờ" dưới một cái giờ mình tự bịa là điều tệ nhất có thể làm ở đây.
      if (!targetSlot) {
        setPendingSlot(null)
        setSelectedSlot(null)
        setConfirmSlotOpen(false)
        setStage('choose_slot')
        setActiveView('schedule')
        addMessage('assistant', 'ViVi đã giữ tạm khung giờ này, nhưng chưa đọc lại được chính xác ngày và giờ của nó. Bạn chọn giúp tôi khung giờ trong danh sách bên cạnh để tôi xác nhận đúng thời gian nhé.')
        return true
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

      // Backend trả `full_name`, KHÔNG phải `name` (kiểm chứng 16/08/2026 trên update_draft:
      // booker/driver đều là {id, full_name, phone, email, ...}). Bản cũ đọc `.name` nên nạp
      // lại draft là mất sạch tên người đặt/người lái, và `isComplete` bên dưới luôn sai.
      const draftBookerName = data.booker?.full_name || data.booker?.name || ''
      const draftDriverName = data.driver?.full_name || data.driver?.name || ''
      // Người lái có đầu mối riêng hay không do so sánh dữ liệu backend, không đoán.
      const draftDriverSharesContact = !data.driver
        || (!!data.driver.email && data.driver.email === data.booker?.email
            && (data.driver.phone || '') === (data.booker?.phone || ''))

      // Giữ lại các trường draft KHÔNG mang theo (marketingConsent) bằng cách merge,
      // thay vì thay nguyên object như trước.
      setPerson((current) => ({
        ...current,
        bookingName: draftBookerName,
        driverName: draftDriverName,
        phone: data.booker?.phone || '',
        email: data.booker?.email || '',
        driverSameContact: draftDriverSharesContact,
        driverPhone: draftDriverSharesContact ? '' : (data.driver?.phone || ''),
        driverEmail: draftDriverSharesContact ? '' : (data.driver?.email || ''),
        hasLicense: !!data.license_declaration?.has_driving_license,
      }))

      if (stage === 'choose_slot' || stage === 'choose_showroom' || stage === 'need_address') {
        if (data.showroom) {
          const [mappedShowroom] = mapShowrooms([data.showroom], selectedCarId)
          setNearbyShowrooms((current) => current.some((item) => item.id === mappedShowroom.id) ? current : [...current, mappedShowroom])
          setShowroomId(mappedShowroom.id)
        }

        // Draft CÓ trả slot_date/slot_time thật (lifecycle.py::_draft đọc từ bảng
        // test_drive_slots), nên ưu tiên dữ liệu backend, sau đó mới tới slot đang hiển thị.
        // Không còn chuỗi '21:00 - 22:00' ghi cứng: thiếu giờ thì coi như chưa xác định
        // được slot và quay lại bước chọn giờ.
        const foundSlot = findSlotById(slots, data.slot_id)
        const targetSlot = (data.slot_id && data.slot_time && data.slot_date)
          ? { slotId: data.slot_id, time: data.slot_time, dateLabel: data.slot_date }
          : foundSlot

        if (!targetSlot) {
          setPendingSlot(null)
          setSelectedSlot(null)
          setConfirmSlotOpen(false)
          setActiveView('schedule')
          setStage('choose_slot')
          addMessage('assistant', 'ViVi chưa đọc lại được chính xác ngày giờ của khung giờ đang giữ. Bạn chọn giúp ViVi một khung giờ trong danh sách bên cạnh nhé.')
          return true
        }

        setPendingSlot(targetSlot)
        setSelectedSlot(targetSlot)
        setConfirmSlotOpen(true)
        setActiveView('schedule')
        setStage('choose_slot')
        return
      }

      const isComplete = draftBookerName && data.booker?.email && data.license_declaration?.has_driving_license
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
        reply(`ViVi chưa tìm thấy showroom có ${car.name} gần “${detail}”. Bạn hãy nhập địa chỉ khác, kèm phường/xã và tỉnh/thành phố.`)
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
          setInlineOtpDigits(['', '', '', '', '', ''])
          setInlineOtpError('')
          setInlineOtpChallengeId('')
          setInlineOtpMock('')
          setInlineOtpBusy(false)
          setStage('choose_slot')
          setActiveView('schedule')
          addMessage('assistant', 'Khung giờ ViVi giữ tạm cho bạn đã hết hạn. Bạn chọn lại một khung giờ khác để tôi tiếp tục đặt lịch nhé.')
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

  const addMessage = (role, text, extra = {}) => {
    // TODO [BACKEND/AGENT]: Use server message ids and timestamps. Store structured
    // cards/actions separately from display text so UI choices stay deterministic.
    setMessages((current) => [...current, { id: `${Date.now()}-${current.length}`, role, text, ...extra }])
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
      'Xin chào, ViVi là trợ lý đặt lịch lái thử VinFast. ViVi có thể tạo lịch mới hoặc hỗ trợ tra cứu, bổ sung và huỷ lịch đã đặt.',
    )
    if (car) {
      setStage('need_address')
      setActiveView('car')
      primeLocationSuggestions(car)
      reply(`Bạn đang xem ${car.name}. Hãy nhập địa chỉ theo phường/xã và tỉnh/thành phố để ViVi tìm showroom có xe lái thử gần bạn.`, 520)
    } else {
      setStage('need_car')
      setActiveView('agent')
      reply('Trước tiên, bạn muốn lái thử mẫu xe nào? Bạn có thể chọn một mẫu ngay phía trên ô nhập hoặc nhắn tên xe cho ViVi.', 520)
    }
  }

  const chooseCar = (car, fromPrompt = false) => {
    if (interaction.mode === BookingMode.MANAGE_BOOKING) {
      clearManagementContext({ event: InteractionEvent.VIEW_VEHICLE })
    }
    setSelectedCarId(car.id)
    setWorkspaceHidden(false)
    if (!fromPrompt) addMessage('user', `Tôi muốn lái thử ${car.name}.`)
    resetSelectionForVehicleChange()
    setStage('need_address')
    setActiveView('car')
    primeLocationSuggestions(car)
    reply(`Đã chọn ${car.name}. Bây giờ bạn hãy nhập địa chỉ theo phường/xã và tỉnh/thành phố để tôi tìm showroom gần nhất.`)
  }

  // Đổi mẫu xe sẽ quay lại bước địa chỉ để Agent kiểm tra tồn xe/showroom lại từ đầu.
  const switchCar = (car) => {
    setSwitcherOpen(false)
    if (!car || car.id === selectedCarId) return

    if (interaction.mode === BookingMode.MANAGE_BOOKING) {
      clearManagementContext({ event: InteractionEvent.VIEW_VEHICLE })
    }

    setSelectedCarId(car.id)
    addMessage('user', `Tôi muốn đổi sang ${car.name}.`)
    resetSelectionForVehicleChange()
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
    const requestId = showroomRequestRef.current + 1
    showroomRequestRef.current = requestId

    setWorkspaceHidden(false)
    setShowroomId(showroom.id)
    // Dọn khung giờ của showroom TRƯỚC khi hỏi showroom mới. Nếu để nguyên, trong lúc chờ
    // mạng người dùng vẫn thấy danh sách giờ của showroom cũ trong khi tên showroom đã đổi
    // — bấm vào là giữ chỗ ở showroom này nhưng phiếu ghi showroom kia.
    setSlots([])
    setPendingSlot(null)
    setSelectedSlot(null)
    setBackendError('')
    setAgentTyping(true)
    try {
      const result = await searchBookingOptions({ vehicleModel: selectedCar.name, showroomId: showroom.id })
      if (showroomRequestRef.current !== requestId) return // đã có lượt chọn mới hơn
      const grouped = groupSlots(result.slots || [])
      setSlots(grouped)
      setStage('choose_slot')
      setActiveView('schedule')
      setAgentTyping(false)
      reply(`${showroom.name} đã được chọn. ViVi đã tìm thấy ${result.slots?.length || 0} khung giờ trống cho bạn.`)
    } catch (error) {
      if (showroomRequestRef.current !== requestId) return
      setAgentTyping(false)
      // Lỗi thì trả về đúng bước chọn showroom với trạng thái sạch: không showroom nào
      // đang được chọn, không khung giờ nào đang hiển thị.
      setShowroomId('')
      setSlots([])
      setStage('choose_showroom')
      setActiveView('map')
      reply(`Không tải được lịch trống của ${showroom.name}: ${error.message}. Bạn chọn lại showroom giúp tôi nhé.`)
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

    const mentionedCar = isDriverChat ? null : resolveAgentCar(value)
    if (mentionedCar) {
      if (!recipient) setRecipient('self')
      setWorkspaceHidden(false)
      if (interaction.mode === BookingMode.MANAGE_BOOKING) {
        clearManagementContext({ resetConversation: true, event: InteractionEvent.VIEW_VEHICLE })
      } else {
        dispatchInteraction({ type: InteractionEvent.VIEW_VEHICLE })
      }
      setSelectedCarId(mentionedCar.id)
    }
    setCheckingVehicleName(mentionedCar?.name || '')

    setAgentTyping(true)
    try {
      const result = isDriverChat
        ? await sendDriverChatMessage(value, {
          conversationId: driverConversationIdRef.current,
          invitationToken: driverInvitationToken,
        })
        : await sendBookingMessage(value, {
        mode: interaction.mode,
        phase: interaction.phase,
        stage,
        allowedActions,
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
      if (isDriverChat) {
        driverConversationIdRef.current = result.conversation_id || driverConversationIdRef.current
        addMessage('assistant', result.response)
        return
      }
      if (mentionedCar && result.intent === 'vehicle_info') {
        if (interaction.mode === BookingMode.MANAGE_BOOKING) {
          clearManagementContext({ event: InteractionEvent.VIEW_VEHICLE })
        }
        setSelectedCarId(mentionedCar.id)
        resetSelectionForVehicleChange()
        setStage('need_address')
        setActiveView('car')
        primeLocationSuggestions(mentionedCar)
      }
      const handledMessage = await applyAgentToolResult(result)
      if (!handledMessage) addMessage('assistant', result.response)
    } catch (error) {
      addMessage('assistant', `Không thể kết nối ViVi: ${error.message}`)
    } finally {
      setAgentTyping(false)
      setCheckingVehicleName('')
      sendingRef.current = false
      setIsSending(false)
    }
  }

  const startLookup = ({ addUserMessage = true, email = '' } = {}) => {
    // ĐÃ XONG: tra cứu chạy thật qua requestBookingAccess + verifyBookingAccess
    // (OTP gửi bằng email). Chỉ sau khi xác thực mới mở được sửa/huỷ/đổi lịch.
    // TODO [BACKEND/ENDPOINT — P0]: các action này vẫn đi qua /api/v1/demo/action;
    // cần endpoint mang tên thật cho nghiệp vụ production.
    if (addUserMessage) addMessage('user', 'Tôi muốn tra cứu lịch đã đặt.')
    dispatchInteraction({ type: InteractionEvent.START_LOOKUP })
    setWorkspaceHidden(false)
    setAccessError('')
    otpChallengeIdRef.current = ''
    // A lookup/edit session also needs reschedule permission for the calendar
    // icon. The backend grants update_details as part of this purpose.
    setAccessValue((current) => ({ ...current, bookingCode: '', email: email || current.email, otpCode: '' }))
    // Xin purpose 'manage': một lần OTP là có đủ quyền xem, đổi giờ VÀ huỷ lịch.
    // Trước đây xin 'reschedule' nên phiên không bao giờ có 'cancel_booking', khiến nút
    // "Huỷ lịch" trong danh sách không bao giờ hiện (nút gate theo allowed_actions của backend).
    setAccessFlow({ phase: 'request', purpose: 'manage', challengeId: '', expiresAt: 0 })
    reply('Để bảo vệ lịch của bạn, hãy nhập email đã đăng ký. ViVi sẽ gửi OTP qua email.')
  }

  /**
   * Deep-link `/booking?lookup=1` — mở thẳng luồng tra cứu lịch đã đặt.
   *
   * Trang chủ cần một lối vào cho khách QUAY LẠI (xem/đổi/huỷ lịch), nhưng trước đây
   * `/booking` chỉ nhận `?car=` nên không có cách nào trỏ thẳng vào bước tra cứu —
   * người dùng buộc phải vào luồng đặt mới rồi tự tìm đường sang.
   *
   * Bỏ qua luôn hộp "Bạn đặt lịch cho ai": câu đó chỉ có nghĩa với người đang đặt MỚI.
   */
  const lookupRequested = searchParams.get('lookup')
  useEffect(() => {
    if (!lookupRequested) return
    if (interaction.mode === BookingMode.MANAGE_BOOKING) return
    setRecipient((current) => current || 'self')
    setResumePending(false)
    startLookup({ addUserMessage: false })
    // Chỉ chạy khi URL đổi; startLookup được dựng lại mỗi lần render nên không đưa vào deps.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lookupRequested])

  const addBookingToCalendar = () => {
    addMessage('user', 'Thêm buổi lái thử vào lịch của tôi.')

    let carToUse = selectedCar
    let showroomToUse = selectedShowroom
    let slotToUse = selectedSlot
    let codeToUse = bookingCode
    let advisorToUse = bookingAdvisor

    if (!slotToUse || !carToUse || !showroomToUse) {
      try {
        const storedStr = window.sessionStorage.getItem('LAST_CONFIRMED_BOOKING')
        if (storedStr) {
          const stored = JSON.parse(storedStr)
          carToUse = carToUse || stored.car
          showroomToUse = showroomToUse || stored.showroom
          slotToUse = slotToUse || stored.slot
          codeToUse = codeToUse || stored.bookingCode
          advisorToUse = advisorToUse || stored.advisor
        }
      } catch (e) {
        console.error('Lỗi đọc LAST_CONFIRMED_BOOKING:', e)
      }
    }

    const gcalUrl = buildGoogleCalendarUrl({
      car: carToUse,
      showroom: showroomToUse,
      slot: slotToUse,
      bookingCode: codeToUse,
      advisor: advisorToUse,
    })

    if (gcalUrl) {
      window.open(gcalUrl, '_blank', 'noopener,noreferrer')
      reply('ViVi đã mở sẵn trang Google Calendar với đầy đủ thông tin buổi lái thử cho bạn. Bạn chỉ cần bấm "Lưu" để hoàn tất nhé!')
    } else {
      reply('ViVi chưa đọc được chính xác mốc thời gian của buổi hẹn nên chưa mở được Google Calendar. Bạn xem giờ hẹn trên phiếu bên cạnh giúp ViVi nhé.')
    }
  }

  const bookAnotherVehicle = () => {
    addMessage('user', 'Tôi muốn đặt thêm lịch cho một mẫu xe khác.')
    window.sessionStorage.removeItem('LAST_CONFIRMED_BOOKING')
    setBookingCode('')
    setBookingAdvisor(null)
    setSelectedCarId('')
    resetSelectionForVehicleChange()
    setStage('need_car')
    setActiveView('agent')
    setSwitcherOpen(true)
    reply('Được ngay. Lịch vừa đặt vẫn được giữ nguyên, bạn tra cứu lại bất cứ lúc nào bằng email đã đăng ký. Bây giờ bạn muốn lái thử mẫu nào?')
  }

  const changeAccessValue = (field, value) => {
    if (field === 'otpCode') otpCodeRef.current = value
    setAccessValue((current) => ({ ...current, [field]: value }))
  }

  const requestAccessOtp = async (event) => {
    event?.preventDefault()
    setAccessBusy(true); setAccessError('')
    try {
      const result = await requestBookingAccess({ bookingCode: accessValue.bookingCode.trim(), email: accessValue.email.trim(), purpose: accessFlow?.purpose || 'update_details' })
      if (!result?.challenge_id || !result?.expires_at) {
        throw new Error('ViVi chưa mở được phiên xác thực OTP cho bạn. Bạn bấm gửi lại mã giúp ViVi nhé.')
      }
      const expiresAt = new Date(result.expires_at).getTime()
      if (Number.isNaN(expiresAt)) {
        throw new Error('ViVi đọc không được thời hạn của mã OTP này. Bạn bấm gửi lại mã giúp ViVi nhé.')
      }
      otpChallengeIdRef.current = result.challenge_id
      setAccessFlow((current) => ({ phase: 'verify', purpose: current?.purpose || 'update_details', challengeId: result.challenge_id, expiresAt }))
      dispatchInteraction({ type: InteractionEvent.ACCESS_VERIFY })
      otpCodeRef.current = ''
      setAccessValue((current) => ({ ...current, otpCode: '' }))
      setAccessSecondsLeft(Math.max(0, Math.ceil((expiresAt - Date.now()) / 1000)))
      setResendSecondsLeft(result.retry_after_seconds || 60)
      const mockOtp = result.is_mock ? result.otp_code : ''
      addMessage(
        'assistant',
        mockOtp
          ? `Mã OTP mock của bạn là **${mockOtp}**. Nhập mã này để tiếp tục luồng kiểm thử.`
          : 'ViVi đã gửi mã OTP qua email. Bạn vui lòng nhập mã để tiếp tục.',
      )
    } catch (error) {
      // Hai mã giới hạn KHÁC nhau và trước đây chỉ bắt một: OTP_RATE_LIMITED là cooldown
      // ngắn giữa 2 lần gửi, RATE_LIMIT_EXCEEDED là khoá dài theo giờ. Không khoá nút ở
      // trường hợp thứ hai thì người dùng bấm tiếp và mỗi lần bấm lại gia hạn thêm khoá.
      if (error.code === 'OTP_RATE_LIMITED' || error.code === 'RATE_LIMIT_EXCEEDED') {
        const seconds = Number(error.message.match(/\d+/)?.[0] || 0)
        if (seconds > 0) setResendSecondsLeft(seconds)
      }

      const message = accessErrorMessage(error)
      // Hiện NGAY CẠNH form (role="alert") chứ không chỉ thả vào khung chat: form báo lỗi
      // ở đâu thì người dùng tìm ở đó. Bản cũ còn setAccessError('') làm form sạch trơn.
      setAccessError(message)
      addMessage('assistant', message)
    } finally { setAccessBusy(false) }
  }

  const verifyAccessOtp = async (otpOverride = '') => {
    const challengeId = otpChallengeIdRef.current || accessFlow?.challengeId
    if (!challengeId) {
      setAccessError('')
      addMessage('assistant', 'Phiên xác thực của bạn chưa sẵn sàng hoặc đã hết hạn. Bạn bấm gửi lại mã để tôi cấp mã mới nhé.')
      return
    }
    setAccessBusy(true); setAccessError('')
    try {
      const otpCode = typeof otpOverride === 'string' && otpOverride ? otpOverride : otpCodeRef.current
      const verified = await verifyBookingAccess({ challengeId, otpCode })
      completeOtpChallenge()
      const bookings = await listVerifiedBookings({ accessToken: verified.access_session_token })
      const formattedBookings = (bookings.data || bookings || []).map(formatBookingSummary)
      setAccessibleBookings(formattedBookings)
      setWorkspaceHidden(false)
      setActiveView('bookings')
      const accessPurpose = accessFlow?.purpose || 'lookup'
      const isCancellation = accessPurpose === 'cancel'

      if (accessPurpose === 'confirm_booking') {
        const actionKey = `${bookingId}:${bookingVersion}`
        const uiActionId = confirmActionIdsRef.current.get(actionKey) || actionId('confirm')
        confirmActionIdsRef.current.set(actionKey, uiActionId)
        const confirmed = await confirmHeldBooking({ bookingId, version: bookingVersion, uiActionId })
        confirmActionIdsRef.current.delete(actionKey)
        setSubmitting(false)
        setBookingCode(confirmed.booking_code)
        setBookingAdvisor(confirmed.advisor || null)
        setAccessFlow(null)
        setSuccessCinematic(true)
        addMessage('assistant', 'Xác thực OTP thành công! Lịch đặt lái thử của bạn đã được xác nhận chính thức.')
        return
      }

      if (formattedBookings.length > 1) {
        setAccessProfile({
          accessToken: verified.access_session_token,
          accessPurpose,
          bookingId: verified.booking_id,
          bookingCode: '',
          bookerName: '',
          driverName: '',
          phone: '',
          email: accessValue.email,
          permissions: verified.permissions || [],
          allowedActions: [],
          vehicleName: '',
          vehicleModelId: '',
          showroomName: '',
          showroomId: '',
          showroomAddress: '',
          advisorName: '',
          advisorPhone: '',
          slotTime: '',
          slotDate: '',
        })
        setExpandedBookingId('')
        setAccessFlow(null)
        dispatchInteraction({ type: InteractionEvent.ACCESS_LIST })
        otpChallengeIdRef.current = ''
        otpCodeRef.current = ''
        addMessage('assistant', `Xác thực thành công. Tôi tìm thấy ${formattedBookings.length} lịch hợp lệ với email này, bạn chọn lịch muốn xem hoặc chỉnh sửa nhé.`)
        return
      }

      if (formattedBookings.length === 0) {
        clearManagementContext({ resetConversation: false })
        addMessage('assistant', 'Bạn đã xác thực thành công, nhưng tôi chưa tìm thấy lịch nào còn hiệu lực với email này.')
        return
      }

      const booking = await getVerifiedBooking({ accessToken: verified.access_session_token, bookingId: formattedBookings[0]?.id || verified.booking_id })
      setAccessProfile({
        accessToken: verified.access_session_token,
        accessPurpose,
        bookingId: booking.id,
        bookingCode: booking.booking_code || '',
        bookerName: booking.booker?.full_name || '',
        driverName: booking.driver?.full_name || '',
        phone: booking.driver?.phone || booking.booker?.phone || '',
        email: booking.driver?.email || booking.booker?.email || '',
        permissions: verified.permissions || [],
        allowedActions: booking.allowed_actions || [],
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
      setAccessFlow({ phase: isCancellation ? 'confirm_cancel' : 'edit', purpose: accessPurpose, challengeId: '', expiresAt: 0 })
      dispatchInteraction({
        type: isCancellation ? InteractionEvent.ACCESS_CANCEL_CONFIRM : InteractionEvent.ACCESS_EDIT,
      })
      otpChallengeIdRef.current = ''
      otpCodeRef.current = ''
      addMessage('assistant', isCancellation ? 'Xác thực thành công. Vui lòng kiểm tra phiếu bên dưới và xác nhận nếu bạn muốn hủy lịch.' : 'Bạn đã xác thực thành công. Bạn có thể cập nhật thông tin lịch đã đặt ngay bên dưới.')
    } catch (error) { setAccessError(''); addMessage('assistant', error.message) } finally { setAccessBusy(false) }
  }

  const cancelAccessOtp = () => {
    clearManagementContext({ event: InteractionEvent.CANCEL_ACCESS })
    addMessage('assistant', 'ViVi đã dừng bước xác thực rồi. Khi nào bạn cần xem hoặc chỉnh sửa lịch, bạn cứ nhắn cho ViVi nhé.')
  }
  const closeBookingDetails = () => {
    clearManagementContext({ event: InteractionEvent.CLOSE_BOOKING_DETAILS })
    addMessage('assistant', 'ViVi đã đóng phần quản lý lịch. Bạn có thể tiếp tục xem xe hoặc bắt đầu một yêu cầu khác.')
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
    resetBookingConversation()
    window.location.reload()
  }

  const selectAccessibleBooking = async (summary) => {
    if (!accessProfile?.accessToken) return
    setAccessBusy(true); setAccessError('')
    try {
      const booking = await getVerifiedBooking({ accessToken: accessProfile.accessToken, bookingId: summary.id })
      const selectedProfile = { ...accessProfile, bookingId: booking.id, bookingCode: booking.booking_code || '', bookerName: booking.booker?.full_name || '', driverName: booking.driver?.full_name || '', phone: booking.driver?.phone || booking.booker?.phone || '', email: booking.driver?.email || booking.booker?.email || '', allowedActions: booking.allowed_actions || [], vehicleName: booking.vehicle?.name || '', vehicleModelId: booking.vehicle?.id || '', showroomName: booking.showroom?.name || '', showroomId: booking.showroom?.id || '', showroomAddress: booking.showroom?.address || '', advisorName: booking.advisor?.full_name || 'Chưa phân công', advisorPhone: booking.advisor?.phone || '', slotTime: booking.slot_time || '', slotDate: booking.slot_date || '' }
      setAccessProfile(selectedProfile)
      setExpandedBookingId(booking.id)
      setAccessFlow({ phase: accessProfile.accessPurpose === 'cancel' ? 'confirm_cancel' : 'edit', purpose: accessProfile.accessPurpose || 'lookup', challengeId: '', expiresAt: 0 })
      dispatchInteraction({ type: accessProfile.accessPurpose === 'cancel' ? InteractionEvent.ACCESS_CANCEL_CONFIRM : InteractionEvent.ACCESS_EDIT })
      return selectedProfile
    } catch (error) { setAccessError(error.message) } finally { setAccessBusy(false) }
  }

  /**
   * Mở popup huỷ lịch NGAY TRONG danh sách tra cứu.
   * Trước đây chỉ vào được popup này khi ngay từ đầu người dùng chọn mục đích "huỷ"; ai đang
   * xem lịch mà muốn huỷ thì phải thoát ra làm lại từ bước xác thực. Dùng lại đúng
   * CancellationConfirmModal đã có, không dựng popup mới.
   */
  const beginAccessibleCancellation = async (summary) => {
    const targetProfile = summary.id === accessProfile?.bookingId
      ? accessProfile
      : await selectAccessibleBooking(summary)
    if (!targetProfile) return
    setAccessError('')
    setAccessFlow({ phase: 'confirm_cancel', purpose: 'cancel', challengeId: '', expiresAt: 0 })
    dispatchInteraction({ type: InteractionEvent.ACCESS_CANCEL_CONFIRM })
  }

  /**
   * Thoát luồng đổi giờ, quay về danh sách lịch đã đặt.
   * Trước đây vào tới bảng chọn giờ mới là KẸT: không có nút lùi, muốn xem lịch khác phải
   * tải lại trang và xác thực OTP từ đầu.
   */
  const exitReschedule = () => {
    setRescheduleState(null)
    setAccessError('')
    setAccessFlow({ phase: 'edit', purpose: accessProfile?.accessPurpose || 'lookup', challengeId: '', expiresAt: 0 })
    dispatchInteraction({ type: InteractionEvent.ACCESS_EDIT })
  }

  /**
   * Bấm "Giữ lại lịch" trong popup huỷ thì QUAY VỀ danh sách, không thoát hẳn.
   * Dùng closeBookingDetails như trước sẽ xoá sạch ngữ cảnh quản lý lịch — người dùng chỉ
   * lỡ mở nhầm popup mà bị đá ra khỏi cả luồng tra cứu, phải xác thực OTP lại từ đầu.
   */
  const dismissCancellation = () => {
    setAccessError('')
    setAccessFlow({ phase: 'edit', purpose: accessProfile?.accessPurpose || 'lookup', challengeId: '', expiresAt: 0 })
    dispatchInteraction({ type: InteractionEvent.ACCESS_EDIT })
  }

  const changeAccessProfile = (field, value) => setAccessProfile((current) => ({ ...current, [field]: value }))
  const saveAccessProfile = async (event) => {
    event.preventDefault()
    if (!accessProfile) return
    if (rescheduleState?.step === 'pending') {
      setRescheduleState((current) => ({ ...current, step: 'confirm' }))
      dispatchInteraction({ type: InteractionEvent.RESCHEDULE_CONFIRM })
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
      clearManagementContext({ event: InteractionEvent.CLOSE_BOOKING_DETAILS })
      addMessage('assistant', 'ViVi đã cập nhật thông tin đặt lịch của bạn.')
    } catch (error) { setAccessError(error.message) } finally { setAccessBusy(false) }
  }

  const confirmCancellation = async () => {
    if (!accessProfile) return
    setAccessBusy(true); setAccessError('')
    try {
      const cancelled = await cancelVerifiedBooking({ bookingId: accessProfile.bookingId, accessToken: accessProfile.accessToken })
      // Chỉ báo đã huỷ khi BACKEND nói là đã huỷ. Trước đây bỏ qua hoàn toàn response nên
      // bất kỳ phản hồi thành công một phần nào cũng bị hiển thị thành "đã huỷ xong".
      if (cancelled?.booking_status && cancelled.booking_status !== 'cancelled') {
        setAccessError(`Lịch chưa được huỷ (trạng thái hiện tại: ${cancelled.booking_status}). ViVi thử lại hoặc gọi hotline giúp bạn nhé.`)
        return
      }
      clearManagementContext()
      addMessage('assistant', `ViVi đã hủy lịch ${accessProfile.bookingCode}. Khung giờ đã được mở lại.`)
    } catch (error) { setAccessError(error.message) } finally { setAccessBusy(false) }
  }

  const loadRescheduleSlots = async (car, showroom) => {
    setAccessBusy(true); setAccessError('')
    try {
      const result = await searchBookingOptions({ vehicleModel: car.name, showroomId: showroom.id })
      const slots = result.slots || []
      if (slots.some((slot) => slot.status === 'available')) {
        setRescheduleState({ step: 'schedule', car, showroom, slots })
        dispatchInteraction({ type: InteractionEvent.RESCHEDULE_SLOT })
      }
      else {
        const alternatives = await searchBookingOptions({ vehicleModel: car.name })
        setRescheduleState({ step: 'showroom', car, showrooms: alternatives.showrooms || [] })
        dispatchInteraction({ type: InteractionEvent.RESCHEDULE_SHOWROOM })
      }
    } catch (error) { setAccessError(error.message) } finally { setAccessBusy(false) }
  }
  const beginTimeReschedule = (targetProfile = accessProfile) => {
    const car = cars.find((item) => item.id === targetProfile?.vehicleModelId)
      || cars.find((item) => normalizeVehicleName(item.name) === normalizeVehicleName(targetProfile?.vehicleName))
    if (car && targetProfile?.showroomId) {
      setSelectedCarId(car.id)
      setWorkspaceHidden(false)
      setAccessFlow((current) => current ? { ...current, phase: 'edit', purpose: 'reschedule' } : { phase: 'edit', purpose: 'reschedule', challengeId: '', expiresAt: 0 })
      dispatchInteraction({ type: InteractionEvent.START_RESCHEDULE })
      loadRescheduleSlots(car, { id: targetProfile.showroomId, name: targetProfile.showroomName })
    } else setAccessError('ViVi chưa xác định được mẫu xe hoặc showroom của lịch này, nên tạm thời chưa đổi lịch được cho bạn.')
  }
  const beginAccessibleReschedule = async (summary) => {
    const targetProfile = summary.id === accessProfile?.bookingId ? accessProfile : await selectAccessibleBooking(summary)
    if (targetProfile) beginTimeReschedule(targetProfile)
  }
  const holdReschedule = async (slot) => {
    setAccessBusy(true); setAccessError('')
    try {
      const held = await holdVerifiedReschedule({ bookingId: accessProfile.bookingId, slotId: slot.id, accessToken: accessProfile.accessToken })
      // KHÔNG ghi đè slotTime/slotDate của accessProfile ở bước này. Lịch cũ vẫn đang là lịch
      // THẬT cho tới khi bấm xác nhận — giữ chỗ mới có thể hết hạn hoặc người dùng đổi ý.
      // Bản cũ ghi đè ngay tại đây nên phiếu hiện giờ mới trong khi backend vẫn giữ giờ cũ,
      // và nếu thoát giữa chừng thì người dùng không còn thấy giờ hẹn thật của mình nữa.
      // Giờ mới đã được RescheduleConfirmModal hiển thị từ chính `state.slot`.
      setRescheduleState((current) => ({ ...current, step: 'pending', slot, newBookingId: held.booking_id }))
      setRescheduleSecondsLeft(Math.max(0, Math.ceil((new Date(held.hold_expires_at).getTime() - Date.now()) / 1000)))
      setExpandedBookingId(accessProfile.bookingId)
      dispatchInteraction({ type: InteractionEvent.RESCHEDULE_CONFIRM })
      addMessage('assistant', 'ViVi đã giữ tạm khung giờ mới và cập nhật trên phiếu. Bạn bấm “Cập nhật thông tin” để kiểm tra, xác nhận toàn bộ lịch.')
    } catch (error) { setAccessError(error.message) } finally { setAccessBusy(false) }
  }
  const confirmReschedule = async () => {
    setAccessBusy(true); setAccessError('')
    try {
      // Đổi lịch CHỈ dời khung giờ. Bản cũ gọi thêm updateVerifiedBooking() ngay trước đó và
      // gây hỏng dữ liệu thật sự: nó gán `phone`/`email` của NGƯỜI ĐẶT cho người lái, nên ai
      // đặt hộ với liên hệ riêng (xem Batch 6) mà đổi lịch là mất sạch liên hệ của người lái.
      // Nó còn đoán "hai người là một" bằng cách SO SÁNH TÊN — hai người trùng tên là sai ngay.
      // Backend không đòi cập nhật hồ sơ trước khi dời lịch: confirm_reschedule chỉ kiểm tra
      // trạng thái hai booking và hạn giữ chỗ (services/booking/management.py).
      await confirmVerifiedReschedule({ bookingId: accessProfile.bookingId, newBookingId: rescheduleState.newBookingId, accessToken: accessProfile.accessToken })
      const startsAt = new Date(rescheduleState.slot.start_at)
      setAccessProfile((current) => ({ ...current, bookingId: rescheduleState.newBookingId, slotTime: startsAt.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', hour12: false }), slotDate: new Intl.DateTimeFormat('vi-VN', { weekday: 'long', day: '2-digit', month: '2-digit' }).format(startsAt) }))
      clearManagementContext({ event: InteractionEvent.FINISH_RESCHEDULE })
      addMessage('assistant', `ViVi đã đổi lịch thành công. Mã lịch ${accessProfile.bookingCode} được giữ nguyên. ViVi đã gửi thông tin lịch mới qua email.`)
    } catch (error) { setAccessError(error.message) } finally { setAccessBusy(false) }
  }

  useEffect(() => {
    if (resendSecondsLeft <= 0 && accessSecondsLeft <= 0) return undefined
    const timer = window.setInterval(() => {
      setAccessSecondsLeft((value) => Math.max(0, value - 1))
      setResendSecondsLeft((value) => Math.max(0, value - 1))
    }, 1000)
    return () => window.clearInterval(timer)
  }, [resendSecondsLeft, accessSecondsLeft])

  useEffect(() => {
    if (!rescheduleState || rescheduleState.step !== 'pending') return undefined
    if (rescheduleSecondsLeft <= 0) {
      setRescheduleState(null)
      dispatchInteraction({ type: InteractionEvent.ACCESS_EDIT })
      addMessage('assistant', 'Thời gian ViVi giữ tạm khung giờ mới đã hết. Lịch cũ của bạn vẫn được giữ nguyên, bạn yên tâm nhé.')
      return undefined
    }
    const timer = window.setInterval(() => setRescheduleSecondsLeft((value) => Math.max(0, value - 1)), 1000)
    return () => window.clearInterval(timer)
  }, [rescheduleState, rescheduleSecondsLeft])

  const changePerson = (field, value) => {
    setPerson((current) => ({ ...current, [field]: value }))
    setFormErrors((current) => ({ ...current, [field]: '' }))
  }

  const inlineOtpCode = inlineOtpDigits.join('')
  const isInlineOtpComplete = inlineOtpCode.length === 6

  const handleInlineOtpDigit = (index, raw) => {
    const digit = raw.replace(/\D/g, '').slice(-1)
    const nextDigits = inlineOtpDigits.map((curr, i) => (i === index ? digit : curr))
    setInlineOtpDigits(nextDigits)
    setInlineOtpError('')
    if (digit && index < 5) {
      document.getElementById(`review-otp-${index + 1}`)?.focus()
    }
  }

  const handleInlineOtpKeyDown = (index, event) => {
    if (event.key === 'Backspace') {
      if (!inlineOtpDigits[index] && index > 0) {
        event.preventDefault()
        const prevIndex = index - 1
        const nextDigits = inlineOtpDigits.map((curr, i) => (i === prevIndex ? '' : curr))
        setInlineOtpDigits(nextDigits)
        setInlineOtpError('')
        document.getElementById(`review-otp-${prevIndex}`)?.focus()
      }
    }
  }

  const handleInlineOtpPaste = (event) => {
    const pasted = event.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    if (pasted) {
      event.preventDefault()
      const pastedArray = Array.from({ length: 6 }, (_, i) => pasted[i] || '')
      setInlineOtpDigits(pastedArray)
      setInlineOtpError('')
      const nextFocus = Math.min(pasted.length, 6) - 1
      document.getElementById(`review-otp-${nextFocus}`)?.focus()
      if (pasted.length === 6 && !submitting) {
        confirmFinalBooking(pasted)
      }
    }
  }

  const requestInlineOtp = async (emailToUse = person.email) => {
    if (!emailToUse || !EMAIL_PATTERN.test(emailToUse.trim())) return
    setInlineOtpBusy(true)
    setInlineOtpError('')
    try {
      const result = await requestBookingAccess({
        bookingCode: bookingId,
        email: emailToUse.trim(),
        purpose: 'confirm_booking',
        preferredChannel: 'email',
      })
      setInlineOtpChallengeId(result.challenge_id)
      otpChallengeIdRef.current = result.challenge_id
      setResendSecondsLeft(result.retry_after_seconds || 60)
      if (result.is_mock && result.otp_code) {
        setInlineOtpMock(result.otp_code)
      }
    } catch (err) {
      setInlineOtpError(accessErrorMessage(err) || 'Chưa gửi được mã OTP. Bạn bấm "Gửi lại OTP" giúp tôi nhé.')
    } finally {
      setInlineOtpBusy(false)
    }
  }

  const confirmFinalBooking = async (overrideCode) => {
    const codeToVerify = typeof overrideCode === 'string' ? overrideCode : inlineOtpCode
    if (codeToVerify.length !== 6 || submitting) return
    const challengeId = inlineOtpChallengeId || otpChallengeIdRef.current
    if (!challengeId) {
      setInlineOtpError('Phiên xác thực chưa sẵn sàng. Bấm "Gửi lại OTP" giúp tôi nhé.')
      return
    }
    setSubmitting(true)
    setInlineOtpError('')
    try {
      // 1. Verify 6-digit OTP
      const verified = await verifyBookingAccess({
        challengeId,
        otpCode: codeToVerify,
      })

      if (!verified || !verified.access_session_token) {
        throw new Error('Mã OTP chưa chính xác, bạn kiểm tra lại nhé.')
      }

      // 2. Confirm booking
      const actionKey = `${bookingId}:${bookingVersion}`
      const uiActionId = confirmActionIdsRef.current.get(actionKey) || actionId('confirm')
      confirmActionIdsRef.current.set(actionKey, uiActionId)
      const confirmed = await confirmHeldBooking({ bookingId, version: bookingVersion, uiActionId })
      confirmActionIdsRef.current.delete(actionKey)
      setSubmitting(false)
      setBookingCode(confirmed.booking_code)
      setBookingAdvisor(confirmed.advisor || null)
      setSuccessCinematic(true)

      try {
        const lastConfirmedData = {
          car: selectedCar,
          showroom: selectedShowroom,
          slot: selectedSlot,
          bookingCode: confirmed.booking_code,
          advisor: confirmed.advisor || null,
          person,
        }
        window.sessionStorage.setItem('LAST_CONFIRMED_BOOKING', JSON.stringify(lastConfirmedData))
      } catch (e) {
        console.error('Lỗi khi lưu LAST_CONFIRMED_BOOKING:', e)
      }
    } catch (err) {
      setSubmitting(false)
      if (err.code === 'HOLD_EXPIRED' || err.code === 'SLOT_NO_LONGER_AVAILABLE') {
        setInlineOtpDigits(['', '', '', '', '', ''])
        setInlineOtpError('')
        setInlineOtpChallengeId('')
        setPendingSlot(null)
        setSelectedSlot(null)
        setBookingId('')
        setBookingVersion(0)
        setStage('choose_slot')
        setActiveView('schedule')
        addMessage('assistant', 'Thời gian giữ tạm khung giờ này đã hết hạn. Bạn vui lòng chọn lại một khung giờ khác nhé.')
        return
      }
      setInlineOtpError(accessErrorMessage(err) || 'Mã OTP chưa đúng, bạn kiểm tra lại giúp tôi nhé.')
    }
  }

  const submitPerson = async (event) => {
    event.preventDefault()
    const errors = {}
    if (person.bookingName.trim().length < 2) errors.bookingName = 'Bạn vui lòng cho tôi biết tên người đứng ra đặt lịch.'
    if (recipient === 'other' && person.driverName.trim().length < 2) errors.driverName = 'Bạn vui lòng cho tôi biết tên người sẽ trực tiếp lái thử.'
    if (person.phone.trim() && !PHONE_PATTERN.test(person.phone.trim())) errors.phone = 'Số điện thoại này chưa đúng định dạng Việt Nam, bạn kiểm tra lại giúp tôi nhé.'
    if (!EMAIL_PATTERN.test(person.email.trim())) errors.email = 'Bạn vui lòng nhập email, và nhập đúng định dạng để tôi gửi xác nhận lịch.'

    if (recipient === 'other' && person.driverSameContact === false) {
      if (!EMAIL_PATTERN.test(person.driverEmail.trim())) {
        errors.driverEmail = 'Bạn vui lòng nhập email của người lái thử, và nhập đúng định dạng.'
      }
      if (person.driverPhone.trim() && !PHONE_PATTERN.test(person.driverPhone.trim())) {
        errors.driverPhone = 'Số điện thoại của người lái thử chưa đúng định dạng, bạn kiểm tra lại nhé.'
      }
    }

    if (!person.hasLicense) errors.hasLicense = 'Bạn vui lòng xác nhận người lái thử có giấy phép lái xe phù hợp trước khi tiếp tục.'
    setFormErrors(errors)
    if (Object.keys(errors).length) return

    setBackendError('')
    try {
      const saved = await saveBookingCustomer({ bookingId, version: bookingVersion, recipient, person })
      setBookingVersion(saved.version)
      setStage('review')
      setActiveView('ticket')
      setInlineOtpDigits(['', '', '', '', '', ''])
      setInlineOtpError('')
      addMessage('user', 'Tôi đã hoàn tất thông tin người lái.')
      reply('ViVi đã lưu phiếu tạm cho bạn. Mã OTP 6 chữ số vừa được gửi qua email. Bạn nhập mã 6 số vào ô bên phải để kích hoạt nút "Xác nhận đặt lịch" nhé.')
      requestInlineOtp(person.email)
    } catch (error) {
      reply(`ViVi chưa lưu được thông tin của bạn: ${error.message}`)
    }
  }

  const submitBooking = async () => {
    setSubmitting(true)
    setAccessError('')
    try {
      const result = await requestBookingAccess({
        bookingCode: bookingId,
        email: person.email,
        purpose: 'confirm_booking',
        preferredChannel: 'email',
      })
      otpChallengeIdRef.current = result.challenge_id
      const expiresAt = result.expires_at ? new Date(result.expires_at).getTime() : Date.now() + 600000
      setAccessFlow({
        phase: 'verify',
        purpose: 'confirm_booking',
        challengeId: result.challenge_id,
        expiresAt,
      })
      dispatchInteraction({ type: InteractionEvent.ACCESS_VERIFY })
      setAccessValue((current) => ({ ...current, email: person.email, otpCode: '' }))
      setAccessSecondsLeft(Math.max(0, Math.ceil((expiresAt - Date.now()) / 1000)))
      setResendSecondsLeft(result.retry_after_seconds || 60)

      const mockOtp = result.is_mock ? result.otp_code : ''
      addMessage(
        'assistant',
        mockOtp
          ? `Mã OTP xác nhận đặt lịch của bạn là **${mockOtp}**. Nhập mã này để chốt lịch chính thức.`
          : `ViVi đã gửi mã OTP xác nhận đặt lịch đến email **${person.email}**. Bạn vui lòng nhập mã để chốt lịch nhé.`,
      )
    } catch (error) {
      reply(`Chưa thể gửi mã OTP xác nhận: ${error.message}`)
    } finally {
      setSubmitting(false)
    }
  }

  // Đặt lịch xong thì thanh tab chỉ còn ĐÚNG 1 nút "Phiếu lịch".
  // Ba tab kia (Đổi mẫu xe, Showroom, Lịch trống) là công cụ của lúc đang đặt; giữ lại sau khi
  // đã có mã lịch thì thanh vừa dài vừa mời khách bấm vào những thứ không còn tác dụng, trong
  // khi renderWorkspace() ở stage 'success' luôn trả về phiếu lịch bất kể activeView là gì.
  // Muốn đổi xe hoặc đổi giờ sau khi đã đặt thì dùng nút "Đổi hoặc huỷ lịch" ở khung chat.
  const viewOptions = workspaceModel.kind === 'new_booking' ? (
    stage === 'success'
      ? (selectedCar && selectedShowroom && selectedSlot
        ? [{ id: 'ticket', label: 'Phiếu lịch', icon: CheckCircle }]
        : [])
      : [
        ...(selectedCar ? [
          { id: 'car', label: 'Đổi mẫu xe', icon: CarProfile },
          ...(nearbyShowrooms.length ? [{ id: 'map', label: 'Showroom', icon: MapPin }] : []),
          ...(selectedShowroom ? [{ id: 'schedule', label: 'Lịch trống', icon: CalendarBlank }] : []),
          ...(stage === 'review' ? [{ id: 'ticket', label: 'Phiếu lịch', icon: CheckCircle }] : []),
        ] : []),
      ]
  ) : accessProfile ? [{ id: 'bookings', label: 'Lịch đã đặt', icon: CalendarBlank }] : []

  /**
   * Tiêu đề của bảng bên trái, hiển thị NGAY TRONG thanh công cụ.
   *
   * Trước đây mỗi bảng tự in tiêu đề trong thân mình, mà thanh công cụ lại `position: absolute`
   * nổi phía trên — nên tiêu đề luôn nằm THẤP hơn hàng nút một khoảng, trông như hai tầng rời
   * nhau. Đưa vào chung một hàng flex là cách duy nhất canh chuẩn được, vì bề rộng thanh công
   * cụ đổi theo số nút (2, 3 hay 4 nút tuỳ bước).
   */
  const workspaceTitle = (() => {
    if (rescheduleState?.step === 'showroom') return 'Chọn showroom khác'
    if (rescheduleState?.car && rescheduleState?.showroom) {
      return `${rescheduleState.car.name} tại ${rescheduleState.showroom.name}`
    }
    if (activeView === 'bookings' && accessProfile) return 'Chọn lịch cần thao tác'
    return ''
  })()

  const renderWorkspace = () => {
    if (activeView === 'bookings' && accessProfile) return <section className="booking-history"><div className="booking-history__list">{accessibleBookings.map((booking) => { const expanded = expandedBookingId === booking.id; const details = booking.id === accessProfile.bookingId ? accessProfile : null; const bookingCodeLabel = booking.booking_code || 'Lịch lái thử'; return <div key={booking.id} className={expanded ? 'is-active is-expanded' : ''}><button type="button" onClick={() => { setExpandedBookingId(expanded ? '' : booking.id); if (!expanded) selectAccessibleBooking(booking) }}><strong>{bookingCodeLabel}</strong><small>{booking.display_time || (booking.start_at ? new Intl.DateTimeFormat('vi-VN', { weekday: 'long', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(booking.start_at)) : 'Lịch lái thử')}</small></button>{expanded && details && <div className="booking-history__details"><p><span>Mẫu xe</span>{details.vehicleName}</p><p><span>Showroom</span>{details.showroomName}<small>{details.showroomAddress}</small></p><p><span>Thời gian</span>{details.slotTime} · {details.slotDate}</p>{rescheduleState?.step === 'pending' && <p className="booking-history__hold"><span>Khung giờ mới đang được giữ</span>Còn lại {Math.floor(rescheduleSecondsLeft / 60)}:{String(rescheduleSecondsLeft % 60).padStart(2, '0')}</p>}<p><span>Tư vấn viên</span>{details.advisorName}<small>{details.advisorPhone || 'Chưa có số điện thoại'}</small></p><div className="booking-history__actions"><span className="booking-history__actions-main">{allowedActions.includes('reschedule') && <button type="button" className="booking-history__action" onClick={() => beginAccessibleReschedule(booking)} aria-label={`Đổi ngày giờ lịch ${bookingCodeLabel}`}><PencilSimple size={13} weight="bold" /> Đổi giờ</button>}{details.allowedActions?.includes('cancel') && <button type="button" className="booking-history__action booking-history__action--danger" onClick={() => beginAccessibleCancellation(booking)} aria-label={`Huỷ lịch ${bookingCodeLabel}`}><Prohibit size={13} weight="bold" /> Huỷ lịch</button>}</span></div></div>}</div> })}</div></section>
    if (rescheduleState?.step === 'showroom') return <section className="studio-schedule"><div className="reschedule-left-grid">{rescheduleState.showrooms.map((showroom) => <button type="button" key={showroom.id} onClick={() => loadRescheduleSlots(rescheduleState.car, showroom)}><strong>{showroom.name}</strong><small>{showroom.address}</small></button>)}</div></section>
    if (rescheduleState?.step === 'schedule') return <SchedulePanel compact onBack={exitReschedule} car={rescheduleState.car} showroom={rescheduleState.showroom} slots={groupSlots(rescheduleState.slots)} pendingSlot={null} onPick={(picked) => holdReschedule(rescheduleState.slots.find((slot) => slot.id === picked.slotId))} />
    if (rescheduleState?.step === 'pending') return <SchedulePanel compact onBack={exitReschedule} car={rescheduleState.car} showroom={rescheduleState.showroom} slots={groupSlots(rescheduleState.slots)} pendingSlot={{ slotId: rescheduleState.slot.id }} onPick={(picked) => holdReschedule(rescheduleState.slots.find((slot) => slot.id === picked.slotId))} />
    if (rescheduleState?.step === 'confirm') return <section className="studio-schedule"><div className="studio-schedule__heading"><span>Đang chờ xác nhận</span><h2>Xác nhận lịch ở cửa sổ bên phải</h2></div></section>
    if (!selectedCar) return null
    // Đặt lịch xong: panel trái giữ NGUYÊN như trước — model xe (3D nếu mẫu đó có) nằm trên,
    // phiếu lịch nằm dưới. Chỉ panel phải đổi từ trang tĩnh về khung chat với ViVi.
    if (stage === 'success' && selectedShowroom && selectedSlot) {
      return (
        <div className="booking-success-documents">
          <VehiclePanel car={selectedCar} />
          <BookingTicket car={selectedCar} showroom={selectedShowroom} slot={selectedSlot} person={person} recipient={recipient} bookingCode={bookingCode} advisor={bookingAdvisor} compact />
        </div>
      )
    }
    if (activeView === 'map') return <BookingShowroomMap car={selectedCar} showrooms={nearbyShowrooms} selectedId={showroomId} onSelect={setShowroomId} onConfirm={chooseShowroom} userLocation={userLocation} />
    if (activeView === 'schedule' && selectedShowroom) return <SchedulePanel car={selectedCar} showroom={selectedShowroom} slots={slots} pendingSlot={pendingSlot} onPick={chooseSlot} />
    if (activeView === 'ticket' && selectedShowroom && selectedSlot) return <BookingTicket car={selectedCar} showroom={selectedShowroom} slot={selectedSlot} person={person} recipient={recipient} bookingCode={bookingCode} advisor={bookingAdvisor} />
    return <VehiclePanel car={selectedCar} />
  }

  const showVehicleChoices = allowedActions.includes('choose_vehicle') && !accessProfile && interaction.mode !== BookingMode.MANAGE_BOOKING

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
    <main id="main-content" className={`agent-booking-page ${workspaceVisible ? 'has-workspace' : 'is-agent-only'} ${stage === 'success' ? 'is-success' : ''} ${successCinematic ? 'is-cinematic' : ''}`}>
      <BookingHeader />

      {workspaceModel.visible && hasWorkspaceContent && workspaceHidden && (
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

      {!recipient && !resumePending && (
        <RecipientModal
          onSelect={beginConversation}
          onLookup={() => {
            // Chọn 'self' chỉ để đóng modal (modal hiện khi chưa có recipient); người dùng
            // đi nhánh tra cứu nên câu "đặt cho ai" chưa cần trả lời lúc này.
            setRecipient('self')
            startLookup({ addUserMessage: false })
          }}
        />
      )}
      {resumePending && <ResumeModal onContinue={resumeConversation} onRestart={restartConversation} />}
      {successCinematic && selectedCar && (
        <BookingSuccessCinematic car={selectedCar} onComplete={completeBookingSuccess} />
      )}

      {/* Đặt lịch xong KHÔNG đổi sang một bố cục khác nữa.
          Trước đây stage 'success' render `booking-success-layout` riêng: panel trái là phiếu,
          panel phải là một trang tĩnh — đoạn hội thoại với ViVi biến mất, người dùng đang nói
          chuyện dở thì đột nhiên mất người đối thoại.
          Nay dùng đúng bố cục 2 màn quen thuộc: TRÁI giữ phiếu lịch (tab "Phiếu lịch" đã có
          sẵn trong viewOptions cho stage success), PHẢI vẫn là khung chat để ViVi tiếp tục
          hướng dẫn và trả lời. Xem completeBookingSuccess() và successActions bên dưới. */}
      <div className={`booking-studio ${workspaceVisible ? 'booking-studio--split' : 'booking-studio--agent'}`}>
          {workspaceVisible && (
            <section className="booking-workspace">
              {/* Hàng công cụ = viên pill chứa các nút + tiêu đề đứng cạnh, cùng một trục ngang. */}
              <div className="workspace-toolbar">
              <div className="workspace-switcher" role="tablist" aria-label="Nội dung hỗ trợ đặt lịch">
                {/* Đang ở giữa luồng đổi giờ thì lối lùi phải nằm NGAY trên thanh công cụ,
                    cùng hàng với "Lịch đã đặt" và "Ẩn bảng", theo thứ tự trái→phải. Đặt trong
                    thân bảng như bản trước thì người dùng phải cuộn mới thấy. */}
                {rescheduleState && (
                  <button
                    type="button"
                    className="workspace-switcher__back"
                    onClick={exitReschedule}
                  >
                    <CaretLeft size={15} weight="bold" /> Chọn lịch khác
                  </button>
                )}
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
              {workspaceTitle && <h2 className="workspace-toolbar__title">{workspaceTitle}</h2>}
              </div>
              <div className="booking-workspace__content" key={activeView}>{renderWorkspace()}</div>
            </section>
          )}

          <section className="vivi-studio">
            <div className="vivi-studio__head">
              <ViViAvatar />
              <div><strong>ViVi</strong><small><span /> {isDriverChat ? 'Hỗ trợ chuẩn bị lái thử' : 'Trợ lý đặt lịch lái thử'}</small></div>
              {allowedActions.includes('start_lookup') && <button type="button" onClick={startLookup}>Tra cứu lịch</button>}
            </div>

            <div className="vivi-studio__messages" ref={messagesRef} aria-live="polite">
              {resumePending ? (
                <div className="vivi-studio__empty"><ViViAvatar /><p>Bạn đang có một phiên đặt lịch đang dở.</p></div>
              ) : messages.length ? messages.map((message, index) => message.type === 'next_steps' ? (
                <div key={message.id} className="vivi-message vivi-message--assistant vivi-message--card">
                  <ViViAvatar compact />
                  <BookingNextSteps slot={selectedSlot} person={person} recipient={recipient} />
                </div>
              ) : (
                <AgentMessage key={message.id} message={message} isLatest={index === messages.length - 1} />
              )) : (
                <div className="vivi-studio__empty"><ViViAvatar /><p>Chọn người lái thử để ViVi bắt đầu.</p></div>
              )}
              {agentTyping && (
                <div className="vivi-message vivi-message--assistant">
                  <ViViAvatar compact />
                  <ViviStatusTyping />
                </div>
              )}
            </div>

            <div className="vivi-studio__composer">
              {backendError && <p className="booking-api-error" role="alert">{backendError}</p>}
              {resumePending ? (
                null
              ) : (['access_request', 'access_verify', 'booking_edit'].includes(composerMode) || accessProfile) && accessFlow?.phase !== 'confirm_cancel' ? (
                <BookingAccessPanel
                  phase={accessFlow?.phase || 'edit'}
                  value={accessValue}
                  onChange={changeAccessValue}
                  onRequest={requestAccessOtp}
                  onVerify={verifyAccessOtp}
                  onResend={requestAccessOtp}
                  onCancelAccess={cancelAccessOtp}
                  onCloseDetails={closeBookingDetails}
                  secondsLeft={accessSecondsLeft}
                  resendLeft={resendSecondsLeft}
                  error={accessError}
                  busy={accessBusy}
                  profile={accessProfile}
                  canUpdate={allowedActions.includes('update_details')}
                  onProfileChange={changeAccessProfile}
                  onProfileSave={saveAccessProfile}
                  onBookingCancel={confirmCancellation}
                />
              ) : (
                <>
              {showVehicleChoices && (
                <BookingUpsell
                  cars={upsellCars}
                  onChoose={chooseCar}
                  onBrowseAll={() => setSwitcherOpen(true)}
                  totalCount={cars.length}
                  headline={upsell.headline}
                  note={upsell.note}
                />
              )}

              <ContextualChoices
                stage={stage}
                allowedActions={allowedActions}
                car={selectedCar}
                locationSuggestions={locationSuggestions}
                showrooms={nearbyShowrooms}
                slots={slots}
                onResolveArea={resolveSuggestedArea}
                onShowroom={chooseShowroom}
                onSlot={chooseSlot}
              />

              {/*
                Hành động sau khi đặt lịch xong.
                Chọn theo đúng thứ một người vừa đặt lịch thật sự cần, KHÔNG phải thứ nghe hay:
                - "Thêm vào lịch" đứng đầu vì bỏ quên buổi hẹn là vấn đề lõi của dự án
                  (nghiên cứu người dùng có một ca no-show thật). Tạo .ics ngay ở frontend nên
                  không phụ thuộc email/OTP.
                - "Đổi hoặc huỷ lịch" vì lo lắng lớn thứ hai là "lỡ bận thì sao".
                - "Đặt thêm mẫu xe khác" cho người đang so sánh nhiều xe.
                KHÔNG thêm nút kiểu "Tôi tới trễ thì sao?" hay "Có mất phí không?" — không có
                API nào trả lời được, mà bịa chính sách cho khách là điều tuyệt đối không làm.
                Những câu đó người dùng vẫn gõ tự do cho ViVi được, và thẻ hướng dẫn phía trên
                đã đưa sẵn hotline + số showroom.
              */}
              {stage === 'success' && (
                <div className="vivi-capabilities vivi-capabilities--success">
                  <button type="button" onClick={addBookingToCalendar}>
                    <CalendarBlank size={14} weight="light" style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                    Thêm vào lịch của tôi
                  </button>
                  <button type="button" onClick={() => startLookup({ addUserMessage: false })}>
                    <ArrowsClockwise size={14} weight="light" style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                    Đổi hoặc huỷ lịch
                  </button>
                  <button type="button" onClick={bookAnotherVehicle}>
                    <CarProfile size={14} weight="light" style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                    Đặt thêm mẫu xe khác
                  </button>
                </div>
              )}

              {/* Hàng nút nhanh ngay trên ô nhập.
                  ĐÃ GỠ 2 nút vì trùng nguyên si với thứ đã có sẵn trên màn hình:
                  - "Tra cứu lịch đã đặt"  → trùng nút "Tra cứu lịch" ở header ViVi (cùng
                    handler startLookup, cùng điều kiện allowedActions.includes('start_lookup')).
                  - "Đổi mẫu xe khác"      → trùng tab "Đổi mẫu xe" ở panel trái, bấm vào cũng
                    mở đúng bảng chọn xe đó.
                  Đừng thêm lại: hai nút này từng làm màn agent có 2 bản của cùng một hành động. */}
              {allowedActions.some((action) => (
                action === 'choose_vehicle' ? !showVehicleChoices : ['use_geolocation', 'view_vehicle'].includes(action)
              )) && (
                <div className="vivi-capabilities">
                  {allowedActions.includes('choose_vehicle') && !showVehicleChoices && (
                    <button type="button" onClick={() => setSwitcherOpen(true)} aria-haspopup="dialog">
                      <CarProfile size={14} weight="light" style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                      Xem tất cả {cars.length} mẫu
                    </button>
                  )}
                  {allowedActions.includes('use_geolocation') && (
                    <button type="button" onClick={requestUserLocation}>
                      <NavigationArrow size={14} weight="light" style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                      Định vị hiện tại
                    </button>
                  )}
                  {allowedActions.includes('view_vehicle') && (
                    <button type="button" onClick={() => setSwitcherOpen(true)} aria-haspopup="dialog">
                      <CarProfile size={14} weight="light" style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                      Xem mẫu xe khác
                    </button>
                  )}
                </div>
              )}

              {timeLeft && (stage === 'collect_info' || stage === 'review') && (
                /* Style nằm ở styles/12-booking-modals.css, KHÔNG đặt inline nữa:
                   bản cũ gán cứng màu cam #e25c00 và font monospace, cả hai đều nằm ngoài
                   hệ màu và bộ chữ của web. */
                <div className="vivi-hold-timer">
                  <Clock size={14} weight="light" aria-hidden="true" />
                  <span>Khung giờ đang được ViVi giữ trong</span>
                  <strong>{timeLeft}</strong>
                </div>
              )}

              {stage === 'collect_info' ? (
                <CustomerForm recipient={recipient} value={person} errors={formErrors} onChange={changePerson} onSubmit={submitPerson} onBack={() => setActiveView('schedule')} />
              ) : stage === 'review' ? (
                <>
                  <div className="vivi-inline-otp">
                    <div className="vivi-inline-otp__header">
                      <span>Xác thực OTP người đặt</span>
                      <small>Mã 6 chữ số vừa gửi tới <strong>{person.email}</strong></small>
                    </div>

                    <div className="vivi-inline-otp__boxes">
                      {inlineOtpDigits.map((digit, index) => (
                        <input
                          key={index}
                          id={`review-otp-${index}`}
                          aria-label={`Mã OTP số ${index + 1}`}
                          className="vivi-inline-otp__box"
                          inputMode="numeric"
                          maxLength={1}
                          value={digit}
                          disabled={submitting}
                          onKeyDown={(e) => handleInlineOtpKeyDown(index, e)}
                          onPaste={handleInlineOtpPaste}
                          onChange={(e) => handleInlineOtpDigit(index, e.target.value)}
                        />
                      ))}
                    </div>

                    <div className="vivi-inline-otp__resend-wrapper">
                      <button
                        type="button"
                        className="vivi-inline-otp__resend-btn"
                        disabled={resendSecondsLeft > 0 || submitting}
                        onClick={() => {
                          setInlineOtpDigits(['', '', '', '', '', ''])
                          setInlineOtpError('')
                          requestInlineOtp(person.email)
                        }}
                      >
                        {resendSecondsLeft > 0 ? `Gửi lại OTP sau ${resendSecondsLeft}s` : 'Gửi lại OTP'}
                      </button>
                    </div>

                    {(inlineOtpError || inlineOtpMock) && (
                      <div className="vivi-inline-otp__error" role="alert">
                        {inlineOtpError ? inlineOtpError : `Mã mock: ${inlineOtpMock}`}
                      </div>
                    )}
                  </div>

                  <div className="vivi-review-actions">
                    <button
                      type="button"
                      onClick={confirmFinalBooking}
                      disabled={!isInlineOtpComplete || submitting}
                      className={isInlineOtpComplete ? 'is-enabled-confirm' : 'is-disabled-confirm'}
                    >
                      {submitting ? 'Đang kiểm tra & chốt lịch...' : 'Xác nhận đặt lịch'} <Check size={16} weight="light" />
                    </button>
                    <button
                      type="button"
                      onClick={() => { setStage('collect_info'); setActiveView('schedule') }}
                    >
                      Chỉnh lại thông tin
                    </button>
                  </div>
                </>
              ) : (
                <form className="vivi-prompt" onSubmit={handlePrompt} aria-busy={composerDisabled}>
                  <label htmlFor="vivi-booking-prompt">Nhắn cho ViVi</label>
                  <div>
                    <textarea id="vivi-booking-prompt" rows="2" value={draft} maxLength={CHAT_MESSAGE_MAX_LENGTH} disabled={composerDisabled} onChange={(event) => setDraft(event.target.value)} placeholder={composerDisabled ? 'ViVi đang thực hiện tác vụ cho bạn' : isDriverChat ? 'Chia sẻ điều bạn muốn chuẩn bị cho buổi lái thử…' : stage === 'need_address' || stage === 'need_ward' ? 'Ví dụ: Phường Bến Nghé, TP. Hồ Chí Minh' : 'Nhập mẫu xe, địa chỉ, showroom hoặc thời gian…'} onKeyDown={(event) => {
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
            </>
          )}
            </div>
          </section>
        </div>

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
          onClose={dismissCancellation}
          busy={accessBusy}
          error={accessError}
        />
      )}
    </main>
  )
}
