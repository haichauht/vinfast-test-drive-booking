/**
 * components/booking/BookingChatPrimitives.jsx — Các mảnh giao diện của khung chat ViVi.
 *
 * - ViViAvatar: ảnh đại diện ViVi, prop `compact` cho bản nhỏ nằm cạnh tin nhắn.
 * - AgentMessage: một bong bóng tin nhắn với hiệu ứng gõ chữ và định vị dòng/chữ in đậm.
 * - ViviStatusTyping: chỉ báo hiệu ứng "ViVi đang thực hiện tác vụ cho bạn".
 * - ContextualChoices: dải nút gợi ý ngay trong khung chat (Showroom / Slot).
 */
import { useEffect, useRef, useState } from 'react'
import { Clock, MapPin } from '@phosphor-icons/react'
import { viviAvatar } from '../../data/media'

const formatDistance = (distance) => (
  Number.isFinite(distance) ? `${String(distance).replace('.', ',')} km` : ''
)

export function ViViAvatar({ compact = false }) {
  return (
    <span className={`${compact ? 'vivi-message__avatar' : 'vivi-studio__avatar'} vivi-avatar`}>
      <img src={viviAvatar} alt="" aria-hidden="true" />
    </span>
  )
}

export function AgentMessage({ message, isLatest }) {
  const [displayedText, setDisplayedText] = useState(
    isLatest && message.role === 'assistant' ? '' : (message.text || '')
  )
  const [isTyping, setIsTyping] = useState(false)
  const hasAnimatedRef = useRef(false)
  const textRef = useRef(message.text)

  useEffect(() => {
    textRef.current = message.text
  }, [message.text])

  useEffect(() => {
    if (message.role !== 'assistant' || !isLatest || hasAnimatedRef.current) return

    const initialText = textRef.current || ''
    if (!initialText) return

    hasAnimatedRef.current = true
    setDisplayedText('')
    setIsTyping(true)
    let index = 0

    const timer = setInterval(() => {
      const currentFullText = textRef.current || ''
      index = Math.min(index + 1, currentFullText.length)
      setDisplayedText(currentFullText.slice(0, index))
      if (index >= currentFullText.length) {
        clearInterval(timer)
        setIsTyping(false)
      }
    }, 16)

    return () => {
      clearInterval(timer)
      setIsTyping(false)
    }
  }, [message.role, isLatest])

  useEffect(() => {
    if (!isTyping) {
      setDisplayedText(message.text || '')
    }
  }, [message.text, isTyping])

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
    <div className={`vivi-message vivi-message--${message.role} ${message.emphasis ? 'vivi-message--emphasis' : ''}`.trim()}>
      {message.role === 'assistant' && <ViViAvatar compact />}
      <div>
        <p>{formatText(displayedText)}</p>
      </div>
    </div>
  )
}

export function ViviStatusTyping() {
  const words = ['ViVi', 'đang', 'thực', 'hiện', 'tác', 'vụ', 'cho', 'bạn']

  return (
    <div className="vivi-typing" aria-label="ViVi đang thực hiện tác vụ cho bạn">
      {words.map((word, index) => (
        <span
          key={`${word}-${index}`}
          className="vivi-typing__word"
          style={{ animationDelay: `${(index * 0.1).toFixed(1)}s` }}
        >
          {word}
        </span>
      ))}
      <span className="vivi-typing__dot" style={{ animationDelay: '0.8s' }} />
      <span className="vivi-typing__dot" style={{ animationDelay: '0.9s' }} />
      <span className="vivi-typing__dot" style={{ animationDelay: '1.0s' }} />
    </div>
  )
}

/**
 * Lọc chính xác các mốc ngày/tháng được ViVi nhắc tới làm mục tiêu khả dụng.
 * Tự động loại bỏ các đoạn văn bản dẫn (VD: "Hôm nay là...", "tuần sau từ 24/08 - 30/08")
 * để tránh highlight nhầm ngày hiện tại hoặc dải ngày đầu/cuối tuần.
 */
export function extractTargetDates(text = '', slots = []) {
  if (!text) return []

  // 1. Loại bỏ các khoảng tuần (dạng "24/08 - 30/08", "24/08 – 30/08", "24/08 đến 30/08")
  let cleanText = text.replace(/(\d{1,2}\/\d{1,2})\s*(?:-|–|đến)\s*(\d{1,2}\/\d{1,2})/gi, '')

  // 2. Loại bỏ hoàn toàn câu dẫn về ngày hiện tại (VD: "Hôm nay là 20/08", "nay là 20/08", "hôm nay 20/08")
  cleanText = cleanText.replace(/(?:hôm\s+)?nay\s+(?:là\s+)?[^,.\n]*?\d{1,2}\/\d{1,2}/gi, '')
  cleanText = cleanText.replace(/\d{1,2}\/\d{1,2}\s*\([^)]*hôm\s+nay[^)]*\)/gi, '')

  // 3. Match tất cả DD/MM còn lại trong câu
  const matches = [...cleanText.matchAll(/(\d{1,2})\/(\d{1,2})/g)]
  const extractedKeys = []

  for (const m of matches) {
    const d = Number(m[1])
    const mo = Number(m[2])
    if (d >= 1 && d <= 31 && mo >= 1 && mo <= 12) {
      const dayNum = String(d).padStart(2, '0')
      const monthNum = String(mo).padStart(2, '0')
      const key = `${monthNum}-${dayNum}`
      if (!extractedKeys.includes(key)) extractedKeys.push(key)
    }
  }

  // 4. Bắt buộc kiểm tra với dữ liệu slots thật từ cơ sở dữ liệu:
  // Chỉ chấp nhận những ngày THỰC SỰ có trong slots và THỰC SỰ còn khung giờ trống (isAvailable = true).
  // Nếu ViVi tự chat ra ngày không có thật hoặc ngày đã kín lịch, ngày đó sẽ bị LOẠI BỎ hoàn toàn.
  if (slots.length && extractedKeys.length > 0) {
    return extractedKeys.filter((key) =>
      slots.some((day) =>
        (day.value?.endsWith(`-${key}`) || day.dateLabel?.includes(key.replace('-', '/'))) &&
        day.times?.some((entry) => entry.isAvailable)
      )
    )
  }

  return []
}

export function ContextualChoices({ stage, allowedActions, car, locationSuggestions, showrooms, slots, pendingSlot, lastMessage, onResolveArea, onShowroom, onSlot }) {
  if (!car) return null

  if (stage === 'need_address' || stage === 'need_ward') {
    return null
  }

  if (stage === 'choose_showroom' && allowedActions.includes('select_showroom') && showrooms.length) {
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

  if (stage === 'choose_slot' && allowedActions.includes('select_slot') && slots.length) {
    const availableDays = slots.filter((day) => day.times.some((entry) => entry.isAvailable))
    // Lấy đúng tin nhắn MỚI NHẤT để định vị chính xác ngày người dùng vừa hỏi
    const lastMsg = Array.isArray(lastMessage) ? lastMessage[lastMessage.length - 1] : lastMessage
    const lastText = String(lastMsg?.text || lastMsg?.content || '')
    const targetKeys = extractTargetDates(lastText, slots)
    const matchedDays = []

    if (pendingSlot?.slotId) {
      const pDay = availableDays.find((day) => day.times.some((entry) => entry.slotId === pendingSlot.slotId))
      if (pDay) matchedDays.push(pDay)
    }

    if (!matchedDays.length && targetKeys.length) {
      for (const key of targetKeys) {
        const found = availableDays.find((day) => day.value?.endsWith(`-${key}`) || day.dateLabel?.includes(key.replace('-', '/')))
        if (found && !matchedDays.some((d) => d.value === found.value)) {
          matchedDays.push(found)
        }
      }
    }

    const quickSlots = []
    const targetDays = matchedDays.length ? matchedDays : availableDays

    for (const day of targetDays) {
      const avail = day.times.filter((entry) => entry.isAvailable)
      // Loại bỏ các mốc giờ trùng lặp trên cùng 1 ngày (ví dụ 09:00 có ở cả bản Eco và Plus)
      const seenTimes = new Set()
      for (const entry of avail) {
        if (!seenTimes.has(entry.time)) {
          seenTimes.add(entry.time)
          quickSlots.push({
            date: day.value,
            dateLabel: day.dateLabel,
            time: entry.time,
            slotId: entry.slotId,
          })
          if (quickSlots.length >= 5) break
        }
      }
      if (quickSlots.length >= 5) break
    }

    const displaySlots = quickSlots.slice(0, 5)

    return (
      <div className="agent-context" aria-label="Khung giờ còn trống">
        <div className="agent-context__heading"><span>Khung giờ gần nhất</span><small>Đã ghép đúng xe {car.name}</small></div>
        <div className="agent-context__rail agent-context__rail--slots">
          {displaySlots.map((slot, idx) => (
            <button type="button" key={slot.slotId || `${slot.date}-${slot.time}-${idx}`} onClick={() => onSlot(slot)}>
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
