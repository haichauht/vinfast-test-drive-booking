import { apiPost } from './client'

const action = (name, payload) => apiPost('/demo/action', { action: name, payload })

export const searchBookingOptions = ({ vehicleModel, showroomId }) => action('search_options', {
  vehicle_model: vehicleModel,
  showroom_id: showroomId,
  limit: 5,
})

export const holdBookingSlot = (slotId) => action('hold_slot', {
  slot_id: slotId,
  ui_action_id: `hold:${crypto.randomUUID()}`,
})

export const saveBookingCustomer = ({ bookingId, version, recipient, person }) => action('update_draft', {
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
  license_patch: { has_valid_license_commitment: person.hasLicense },
})

export const confirmHeldBooking = ({ bookingId, version }) => action('confirm_booking', {
  booking_id: bookingId,
  expected_version: version,
  ui_action_id: `confirm:${crypto.randomUUID()}`,
})
