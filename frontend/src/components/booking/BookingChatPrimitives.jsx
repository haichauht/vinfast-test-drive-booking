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
