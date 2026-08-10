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
 * - saveBookingCustomer(): lưu tên/điện thoại/email người đặt và người lái.
 * - confirmHeldBooking(): chốt đặt lịch, trả về mã lịch.
 *
 * Nhóm 2 — tra cứu/sửa/huỷ lịch đã đặt (qua POST /api/v1/demo/action):
 * - requestBookingAccess() → verifyBookingAccess(): xin và xác thực OTP gửi qua Zalo.
 * - getVerifiedBooking() · updateVerifiedBooking() · cancelVerifiedBooking().
 * - holdVerifiedReschedule() → confirmVerifiedReschedule(): đổi sang khung giờ khác.
 *
 * conversation_id được giữ trong sessionStorage để ViVi nhớ mạch hội thoại trong cùng tab.
 */
import { ApiError, apiPost } from './client'
import { actionId } from './ids'

const CONVERSATION_KEY = 'vinfast:booking-conversation-id'

const readConversationId = () => {
  if (typeof window === 'undefined') return ''
  return window.sessionStorage.getItem(CONVERSATION_KEY) || ''
}

const rememberConversationId = (conversationId) => {
  if (typeof window !== 'undefined' && conversationId) {
    window.sessionStorage.setItem(CONVERSATION_KEY, conversationId)
  }
}

const agentRequest = async ({ message, action, actionPayload = {}, context = {} }) => {
  const result = await apiPost('/chat', {
    message,
    conversation_id: readConversationId(),
    ...(action ? { action } : {}),
    action_payload: actionPayload,
    context: { channel: 'booking', ...context },
  })
  rememberConversationId(result.conversation_id)
  return result
}

const agentAction = async (action, message, actionPayload) => {
  const result = await agentRequest({ message, action, actionPayload })
  if (result.action_error || result.action_data == null) {
    throw new ApiError(result.action_error || result.response || 'Agent không hoàn tất được thao tác đặt lịch.', {
      code: 'AGENT_ACTION_FAILED',
      retryable: true,
    })
  }
  return result.action_data
}

export const sendBookingMessage = (message, context = {}) => agentRequest({ message, context })

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
      ...(person.email ? { email: person.email } : {}),
    },
    driver_same_as_booker: recipient === 'self',
    driver_patch: recipient === 'other'
      ? {
          full_name: person.driverName,
          phone: person.phone,
          ...(person.email ? { email: person.email } : {}),
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

export const requestBookingAccess = ({ bookingCode, phone, purpose = 'lookup' }) => bookingManagementAction('request_access', {
  booking_code: bookingCode,
  contact_value: phone,
  purpose,
  preferred_channel: 'zalo',
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
