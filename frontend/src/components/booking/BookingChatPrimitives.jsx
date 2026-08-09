/**
 * components/booking/BookingChatPrimitives.jsx — Các mảnh giao diện của khung chat ViVi.
 *
 * ⚠️ CẢNH BÁO — CẢ FILE NÀY HIỆN KHÔNG ĐƯỢC DÙNG Ở ĐÂU. Không file nào import nó.
 * BookingPage.jsx đang chạy bản sao riêng của cả 3 component bên dưới (dòng ~264, ~287, ~295).
 * Sửa ở đây sẽ KHÔNG thấy gì đổi trên web — muốn sửa chat ViVi thì vào src/pages/BookingPage.jsx.
 * Đây là phần tách file còn dang dở của bên backend, chưa nối lại vào trang.
 *
 * Nội dung 3 component (để đối chiếu với bản trong BookingPage):
 * - ViViAvatar: ảnh đại diện ViVi, prop `compact` cho bản nhỏ nằm cạnh tin nhắn.
 * - AgentMessage: một bong bóng tin nhắn. Tự xuống dòng theo \n và đổi **chữ** thành in đậm.
 * - ContextualChoices: dải nút gợi ý ngay trong khung chat — hiện tối đa 4 showroom khi
 *   stage = 'choose_showroom', hoặc 5 khung giờ gần nhất khi stage = 'choose_slot'.
 *
 * Khác biệt so với bản trong BookingPage: bản ở đây thiếu nhánh gợi ý khu vực
 * (locationSuggestions / onResolveArea) mà bản đang chạy có.
 */
import { Clock, MapPin } from '@phosphor-icons/react'
import { viviAvatar } from '../../data/media'

export function ViViAvatar({ compact = false }) {
  return (
    <span className={`${compact ? 'vivi-message__avatar' : 'vivi-studio__avatar'} vivi-avatar`}>
      <img src={viviAvatar} alt="" aria-hidden="true" />
    </span>
  )
}

export function AgentMessage({ message }) {
  const formatText = (text) => {
    if (!text) return null
    return text.split('\n').map((line, index) => {
      const html = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      return <span key={index} style={{ display: 'block', minHeight: '1em' }} dangerouslySetInnerHTML={{ __html: html }} />
    })
  }

  return (
    <div className={`vivi-message vivi-message--${message.role}`}>
      {message.role === 'assistant' && <ViViAvatar compact />}
      <div><p>{formatText(message.text)}</p></div>
    </div>
  )
}

export function ContextualChoices({ stage, car, showrooms, slots, onShowroom, onSlot }) {
  if (!car) return null

  if (stage === 'need_address' || stage === 'need_ward') return null

  if (stage === 'choose_showroom' && showrooms.length) {
    return (
      <div className="agent-context" aria-label="Chọn showroom trong cuộc trò chuyện">
        <div className="agent-context__heading"><span>Showroom phù hợp</span><small>Đã ưu tiên có xe trước, khoảng cách sau</small></div>
        <div className="agent-context__rail">
          {showrooms.slice(0, 4).map((showroom) => (
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

  if (stage !== 'choose_slot' || !slots.length) return null
  const quickSlots = slots.flatMap((day) => day.times.slice(0, 1).map((entry) => ({
    date: day.value, dateLabel: day.dateLabel, time: entry.time, slotId: entry.slotId,
  }))).slice(0, 5)
  return (
    <div className="agent-context" aria-label="Khung giờ còn trống">
      <div className="agent-context__heading"><span>Khung giờ gần nhất</span><small>Đã ghép đúng xe {car.name}</small></div>
      <div className="agent-context__rail agent-context__rail--slots">
        {quickSlots.map((slot) => (
          <button type="button" key={`${slot.date}-${slot.time}`} onClick={() => onSlot(slot)}>
            <span><Clock size={16} weight="light" /></span><strong>{slot.time}</strong><small>{slot.dateLabel}</small>
          </button>
        ))}
      </div>
    </div>
  )
}
