import { ApiError, apiPost } from './client'

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

export const searchBookingOptions = ({ vehicleModel, showroomId, address }) => agentAction(
  'search_options',
  showroomId
    ? `Kiểm tra lịch trống cho ${vehicleModel} tại showroom đã chọn.`
    : address
      ? `Tìm showroom có ${vehicleModel} gần địa chỉ ${address}.`
      : `Tìm các khu vực có showroom lái thử ${vehicleModel}.`,
  {
    vehicle_model: vehicleModel,
    showroom_id: showroomId,
    address,
    limit: 5,
  },
)

export const holdBookingSlot = (slotId) => agentAction(
  'hold_slot',
  'Tôi xác nhận chọn khung giờ này. Hãy giữ chỗ giúp tôi.',
  {
    slot_id: slotId,
    ui_action_id: `hold:${crypto.randomUUID()}`,
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

export const confirmHeldBooking = ({ bookingId, version }) => agentAction(
  'confirm_booking',
  'Tôi đã kiểm tra thông tin và xác nhận đặt lịch lái thử.',
  {
    booking_id: bookingId,
    expected_version: version,
    ui_action_id: `confirm:${crypto.randomUUID()}`,
  },
)
