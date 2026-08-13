/**
 * api/booking.js — Toàn bộ lệnh đặt lịch lái thử gửi lên backend, gồm cả tin nhắn cho ViVi.
 *
 * Điểm quan trọng: TẤT CẢ thao tác đặt lịch đều đi qua MỘT endpoint duy nhất
 * POST /api/v1/chat của LangGraph Agent, phân biệt nhau bằng trường `action`.
 * Có `action` thì backend gọi thẳng tool và BỎ QUA LLM — nên luồng đặt lịch vẫn chạy
 * bình thường dù chưa có OpenAI key. Chỉ chat tự do (sendBookingMessage) mới cần key.
 *
 * Nhóm 1 — đặt lịch mới (qua /chat):
 * - sendBookingMessage(): người dùng gõ tin nhắn tự do cho ViVi.
 * - searchBookingOptions(): tìm showroom có đúng mẫu xe + khung giờ trống (theo địa chỉ hoặc GPS).
 * - holdBookingSlot(): giữ chỗ một khung giờ (backend trả hạn giữ, UI đếm ngược).
 * - saveBookingCustomer(): lưu tên/email bắt buộc và số điện thoại nếu có.
 * - confirmHeldBooking(): chốt đặt lịch, trả về mã lịch.
 *
 * Nhóm 2 — tra cứu/sửa/huỷ lịch đã đặt (qua POST /api/v1/demo/action):
 * - requestBookingAccess() → verifyBookingAccess(): xin và xác thực OTP gửi qua email.
 * - getVerifiedBooking() · updateVerifiedBooking() · cancelVerifiedBooking().
 * - holdVerifiedReschedule() → confirmVerifiedReschedule(): đổi sang khung giờ khác.
 *
 * conversation_id được giữ trong sessionStorage để ViVi nhớ mạch hội thoại trong cùng tab.
 */
import { ApiError, apiPost } from './client'
import { actionId } from './ids'

const CONVERSATION_KEY = 'vinfast:booking-conversation-id'
const PUBLIC_ACTION_ERROR_MESSAGES = {
  SLOT_NO_LONGER_AVAILABLE: 'Khung giờ này đã qua hoặc không còn khả dụng, vui lòng chọn giờ khác.',
  HOLD_EXPIRED: 'Thời gian giữ chỗ đã hết hạn, vui lòng chọn lại khung giờ.',
  VEHICLE_NOT_READY: 'Xe demo hiện không sẵn sàng cho khung giờ này, vui lòng chọn lịch khác.',
  VERSION_CONFLICT: 'Thông tin đặt lịch đã thay đổi, vui lòng tải lại và thử lại.',
  INVALID_INPUT: 'Thông tin gửi lên chưa hợp lệ, vui lòng kiểm tra lại.',
  AGENT_ACTION_FAILED: 'Agent không hoàn tất được thao tác đặt lịch.',
}

const readConversationId = () => {
  if (typeof window === 'undefined') return ''
  return window.sessionStorage.getItem(CONVERSATION_KEY) || ''
}

const rememberConversationId = (conversationId) => {
  if (typeof window !== 'undefined' && conversationId) {
    window.sessionStorage.setItem(CONVERSATION_KEY, conversationId)
  }
}

const normalizeAgentContext = (context = {}) => ({
  channel: 'booking',
  mode: String(context.mode || ''),
  phase: String(context.phase || context.stage || ''),
  stage: String(context.stage || ''),
  allowed_actions: Array.isArray(context.allowedActions) ? context.allowedActions : [],
  selected_vehicle_id: context.selectedVehicle?.id || '',
  selected_vehicle_name: context.selectedVehicle?.name || '',
  selected_showroom_id: context.selectedShowroom?.id || '',
  selected_showroom_name: context.selectedShowroom?.name || '',
  selected_slot_id: context.selectedSlot?.slotId || '',
  selected_slot_time: context.selectedSlot?.time || '',
  selected_slot_date: context.selectedSlot?.dateLabel || '',
  booking_id: context.bookingId || '',
  recipient: context.recipient || '',
  nearby_showrooms: Array.isArray(context.nearbyShowrooms)
    ? context.nearbyShowrooms.map(({ id, name }) => ({ id, name })).slice(0, 10)
    : [],
})

const agentRequest = async ({ message, action, actionPayload = {}, context = {} }) => {
  const result = await apiPost('/chat', {
    message,
    conversation_id: readConversationId(),
    ...(action ? { action } : {}),
    action_payload: actionPayload,
    context: normalizeAgentContext(context),
  })
  rememberConversationId(result.conversation_id)
  return result
}

const agentAction = async (action, message, actionPayload) => {
  const result = await agentRequest({ message, action, actionPayload })
  if (result.action_error || result.action_data == null) {
    const code = result.action_error || 'AGENT_ACTION_FAILED'
    throw new ApiError(PUBLIC_ACTION_ERROR_MESSAGES[code] || result.response || PUBLIC_ACTION_ERROR_MESSAGES.AGENT_ACTION_FAILED, {
      code,
      retryable: true,
    })
  }
  return result.action_data
}

export const sendBookingMessage = (message, context = {}) => agentRequest({ message, context })

export const resetBookingConversation = () => {
  if (typeof window !== 'undefined') window.sessionStorage.removeItem(CONVERSATION_KEY)
}

export const searchBookingOptions = ({ vehicleModel, showroomId, showroomQuery, address, latitude, longitude }) => agentAction(
  'search_options',
  showroomId
    ? `Kiểm tra lịch trống cho ${vehicleModel} tại showroom đã chọn.`
    : showroomQuery
      ? `Tìm showroom ${showroomQuery} có ${vehicleModel}.`
    : address
      ? `Tìm showroom có ${vehicleModel} gần địa chỉ ${address}.`
      : latitude && longitude
        ? `Tìm showroom có ${vehicleModel} gần tọa độ GPS.`
        : `Tìm các khu vực có showroom lái thử ${vehicleModel}.`,
  {
    vehicle_model: vehicleModel,
    showroom_id: showroomId,
    showroom_query: showroomQuery,
    address,
    latitude,
    longitude,
    // The weekly calendar needs enough inventory to expose the following week
    // without inventing client-side availability. Backend currently caps this at 30.
    limit: 30,
  },
)

export const holdBookingSlot = (slotId, uiActionId = actionId('hold')) => agentAction(
  'hold_slot',
  'Tôi xác nhận chọn khung giờ này. Hãy giữ chỗ giúp tôi.',
  {
    slot_id: slotId,
    ui_action_id: uiActionId,
  },
)

export const saveBookingCustomer = ({ bookingId, version, recipient, person }) => agentAction(
  'update_draft',
  'Tôi đã hoàn tất thông tin người đặt và người lái.',
  {
    booking_id: bookingId,
    expected_version: version,
    booker_patch: {
      full_name: person.bookingName,
      phone: person.phone,
      email: person.email,
    },
    driver_same_as_booker: recipient === 'self',
    driver_patch: recipient === 'other'
      ? {
          full_name: person.driverName,
          phone: person.phone,
          email: person.email,
        }
      : null,
    has_valid_license_commitment: person.hasLicense,
  },
)

export const confirmHeldBooking = ({ bookingId, version, uiActionId = actionId('confirm') }) => agentAction(
  'confirm_booking',
  'Tôi đã kiểm tra thông tin và xác nhận đặt lịch lái thử.',
  {
    booking_id: bookingId,
    expected_version: version,
    ui_action_id: uiActionId,
  },
)

const bookingManagementAction = async (action, payload) => {
  const result = await apiPost('/demo/action', { action, payload })
  return result
}

export const requestBookingAccess = ({ bookingCode = '', email, purpose = 'lookup' }) => bookingManagementAction('request_access', {
  ...(bookingCode.trim() ? { booking_code: bookingCode.trim() } : {}),
  contact_value: email,
  purpose,
  preferred_channel: 'email',
})

export const verifyBookingAccess = ({ challengeId, otpCode }) => bookingManagementAction('verify_access', {
  challenge_id: challengeId,
  otp_code: otpCode,
})

export const getVerifiedBooking = ({ accessToken, bookingCode, bookingId }) => bookingManagementAction('get_details', {
  access_session_token: accessToken,
  ...(bookingId ? { booking_id: bookingId } : { booking_code: bookingCode }),
})

export const listVerifiedBookings = ({ accessToken }) => bookingManagementAction('list_bookings', {
  access_session_token: accessToken,
})

export const updateVerifiedBooking = ({ bookingId, accessToken, bookerPatch, driverPatch, driverSameAsBooker }) => bookingManagementAction('update_details', {
  booking_id: bookingId,
  access_session_token: accessToken,
  booker_patch: bookerPatch,
  driver_patch: driverPatch,
  driver_same_as_booker: driverSameAsBooker,
})

export const cancelVerifiedBooking = ({ bookingId, accessToken, reason = '' }) => bookingManagementAction('cancel_booking', {
  booking_id: bookingId,
  access_session_token: accessToken,
  ui_action_id: actionId('cancel'),
  reason,
})

export const holdVerifiedReschedule = ({ bookingId, slotId, accessToken }) => bookingManagementAction('hold_reschedule', {
  current_booking_id: bookingId,
  new_slot_id: slotId,
  access_session_token: accessToken,
  ui_action_id: actionId('reschedule-hold'),
})

export const confirmVerifiedReschedule = ({ bookingId, newBookingId, accessToken }) => bookingManagementAction('confirm_reschedule', {
  current_booking_id: bookingId,
  new_booking_id: newBookingId,
  access_session_token: accessToken,
  ui_action_id: actionId('reschedule-confirm'),
})
