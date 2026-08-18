/**
 * components/booking/BookingSummary.jsx — Bảng chọn khung giờ và Phiếu đặt lịch.
 *
 * ✅ ĐANG DÙNG THẬT: BookingPage.jsx import cả 2 component bên dưới.
 *
 * - SchedulePanel: lịch tuần kiểu Calendar (bước 4). User có thể chuyển tuần; từng ô cho
 *   biết đúng mẫu xe còn trống, đã kín, hoặc showroom chưa mở lịch. Lịch do backend trả về,
 *   frontend chỉ dựng các ngày/ô trống để tạo ngữ cảnh và tuyệt đối không tự tạo slot.
 *
 * - BookingTicket: phiếu đặt lịch, dùng ở HAI nơi với giao diện hơi khác nhau —
 *   màn xem lại trước khi đặt (chưa có bookingCode) và màn thành công (prop compact + có mã lịch).
 *   Gồm ảnh xe, 8 dòng thông tin và dòng xác nhận đã có giấy phép lái xe.
 *
 * Tư vấn viên chỉ hiển thị sau khi backend xác nhận và trả về nhân viên được gán thật.
 *
 * Style tương ứng: .studio-schedule và .studio-ticket trong index.css.
 */
import { useEffect, useMemo, useRef, useState } from 'react'
import { useGSAP } from '@gsap/react'
import gsap from 'gsap'
import { CalendarBlank, CaretLeft, CaretRight, CheckCircle, Clock } from '@phosphor-icons/react'
import { VehicleShot } from './VehicleWorkspace'

const WEEKDAY_LABELS = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
const DEFAULT_TIMES = ['09:00', '10:30', '14:00', '15:30']

const parseDateValue = (value) => {
  const [year, month, day] = String(value || '').split('-').map(Number)
  return year && month && day ? new Date(year, month - 1, day, 12) : new Date()
}

const dateKey = (date) => [
  date.getFullYear(),
  String(date.getMonth() + 1).padStart(2, '0'),
  String(date.getDate()).padStart(2, '0'),
].join('-')

const addDays = (date, amount) => {
  const next = new Date(date)
  next.setDate(next.getDate() + amount)
  return next
}

const startOfWeek = (date) => {
  const monday = new Date(date)
  const offset = (monday.getDay() + 6) % 7
  monday.setDate(monday.getDate() - offset)
  monday.setHours(12, 0, 0, 0)
  return monday
}

const timeKey = (value) => String(value || '').slice(0, 5)
const timeAsMinutes = (value) => {
  const [hour, minute] = timeKey(value).split(':').map(Number)
  return (hour * 60) + minute
}

export function SchedulePanel({ car, showroom, slots, pendingSlot, onPick }) {
  const root = useRef(null)
  const direction = useRef(0)
  const today = new Date()
  today.setHours(12, 0, 0, 0)
  const [weekStart, setWeekStart] = useState(today)

  const slotMap = useMemo(() => new Map(slots.map((day) => [day.value, day])), [slots])
  const timeRows = useMemo(() => {
    const values = [...new Set(slots.flatMap((day) => day.times.map((entry) => timeKey(entry.time))))]
    return (values.length ? values : DEFAULT_TIMES).sort((a, b) => timeAsMinutes(a) - timeAsMinutes(b))
  }, [slots])
  const weekDays = useMemo(() => Array.from({ length: 7 }, (_, index) => {
    const date = addDays(weekStart, index)
    const key = dateKey(date)
    const source = slotMap.get(key)
    const availableCount = source?.times.filter((entry) => entry.isAvailable).length || 0
    return {
      date,
      key,
      source,
      availableCount,
      dayNumber: String(date.getDate()).padStart(2, '0'),
      monthNumber: String(date.getMonth() + 1).padStart(2, '0'),
    }
  }), [slotMap, weekStart])

  const weekAvailableCount = weekDays.reduce((total, day) => total + day.availableCount, 0)
  const weekSlotCount = weekDays.reduce((total, day) => total + (day.source?.times.length || 0), 0)
  const weekEnd = weekDays[6]?.date || addDays(weekStart, 6)
  const rangeLabel = `${new Intl.DateTimeFormat('vi-VN', { day: '2-digit', month: '2-digit' }).format(weekStart)} – ${new Intl.DateTimeFormat('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(weekEnd)}`
  const currentPageStart = new Date()
  currentPageStart.setHours(12, 0, 0, 0)
  const nextMonday = startOfWeek(addDays(currentPageStart, 7))
  const lastVisibleDate = addDays(currentPageStart, 30)
  const lastVisibleWeekStart = startOfWeek(lastVisibleDate)
  const isCurrentWeek = dateKey(weekStart) === dateKey(currentPageStart)
  const isLastVisibleWeek = dateKey(weekStart) >= dateKey(lastVisibleWeekStart)
  const weekStamp = weekStart.getTime()

  useEffect(() => {
    const current = new Date()
    current.setHours(12, 0, 0, 0)
    setWeekStart(current)
  }, [car.id, showroom.id])

  useEffect(() => {
    if (!pendingSlot?.slotId) return
    const selectedDay = slots.find((day) => day.times.some((entry) => entry.slotId === pendingSlot.slotId))
    if (selectedDay) setWeekStart(startOfWeek(parseDateValue(selectedDay.value)))
  }, [pendingSlot?.slotId, slots])

  useGSAP(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const amount = direction.current * 24
    gsap.fromTo(
      '.schedule-calendar__day, .schedule-calendar__cell',
      { x: amount, opacity: 0 },
      { x: 0, opacity: 1, duration: 0.46, stagger: 0.012, ease: 'power3.out', clearProps: 'transform,opacity' },
    )
    direction.current = 0
  }, { scope: root, dependencies: [weekStamp, slots.length] })

  const changeWeek = (amount) => {
    direction.current = Math.sign(amount)
    setWeekStart((current) => {
      if (amount > 0 && dateKey(current) === dateKey(currentPageStart)) return nextMonday
      if (amount < 0 && dateKey(current) === dateKey(nextMonday)) return currentPageStart
      return addDays(current, amount * 7)
    })
  }

  const returnToCurrentWeek = () => {
    direction.current = dateKey(currentPageStart) > dateKey(weekStart) ? 1 : -1
    setWeekStart(currentPageStart)
  }

  const selectSlot = (event, day, entry) => {
    if (!entry.isAvailable) return
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      gsap.fromTo(event.currentTarget, { scale: 0.96 }, { scale: 1, duration: 0.52, ease: 'elastic.out(1, 0.48)' })
    }
    onPick({ date: day.key, dateLabel: day.source.dateLabel, time: entry.time, slotId: entry.slotId })
  }

  return (
    <section className="studio-schedule studio-schedule--calendar" aria-label="Lịch lái thử" ref={root}>
      <div className="studio-schedule__heading">
        <span>Lịch có đúng mẫu xe</span>
        <h2>{car.name} tại {showroom.name}</h2>
        <p>Chọn trực tiếp một ô còn xe. Bạn có thể chuyển tuần để xem những ngày xa hơn.</p>
      </div>

      <div className="schedule-calendar">
        <header className="schedule-calendar__toolbar">
          <div className="schedule-calendar__navigation" aria-label="Điều hướng tuần">
            <button type="button" onClick={() => changeWeek(-1)} disabled={isCurrentWeek} aria-label="Xem tuần trước"><CaretLeft size={17} weight="bold" /></button>
            <button type="button" onClick={returnToCurrentWeek} disabled={isCurrentWeek}>Tuần này</button>
            <button type="button" onClick={() => changeWeek(1)} disabled={isLastVisibleWeek} aria-label="Xem tuần sau"><CaretRight size={17} weight="bold" /></button>
          </div>
          <div className="schedule-calendar__range">
            <strong>{rangeLabel}</strong>
            <small>{weekAvailableCount ? `${weekAvailableCount} khung giờ còn xe` : 'Chưa có lịch trống trong tuần này'}</small>
          </div>
          <div className="schedule-calendar__legend" aria-label="Chú thích trạng thái">
            <span><i className="is-available" /> Còn xe</span>
            <span><i className="is-unavailable" /> Đã kín</span>
          </div>
        </header>

        <div className="schedule-calendar__viewport">
          <div className="schedule-calendar__matrix" role="grid" aria-label={`Lịch tuần ${rangeLabel}`}>
            <div className="schedule-calendar__week" role="row">
              <div className="schedule-calendar__time-title" role="columnheader"><Clock size={15} weight="light" /> Giờ</div>
              {weekDays.map((day, index) => {
                const isToday = dateKey(new Date()) === day.key
                return (
                  <div className={`schedule-calendar__day ${isToday ? 'is-today' : ''}`} role="columnheader" key={day.key}>
                    <span>{WEEKDAY_LABELS[index]}</span>
                    <strong>{day.dayNumber}</strong>
                    <small>{day.availableCount ? `${day.availableCount} lịch` : `${day.monthNumber}/${day.date.getFullYear()}`}</small>
                  </div>
                )
              })}
            </div>

            <div className="schedule-calendar__body">
              {timeRows.map((time) => (
                <div className="schedule-calendar__row" role="row" key={time}>
                  <div className="schedule-calendar__time" role="rowheader">{time}</div>
                  {weekDays.map((day) => {
                    const entry = day.source?.times.find((candidate) => timeKey(candidate.time) === time)
                    const active = entry && pendingSlot?.slotId === entry.slotId
                    return (
                      <div className="schedule-calendar__cell" role="gridcell" key={`${day.key}-${time}`}>
                        {entry ? (
                          <button
                            type="button"
                            disabled={!entry.isAvailable}
                            className={`${entry.isAvailable ? 'is-available' : 'is-unavailable'} ${active ? 'is-active' : ''}`.trim()}
                            onClick={(event) => selectSlot(event, day, entry)}
                            aria-label={`${entry.time}, ${day.source.dateLabel}: ${entry.isAvailable ? `${car.name} còn xe` : entry.unavailableLabel}`}
                          >
                            <span />
                            <strong>{entry.isAvailable ? `Có ${car.name}` : entry.unavailableLabel}</strong>
                            <small>{entry.isAvailable ? 'Sẵn sàng lái thử' : 'Không thể chọn'}</small>
                          </button>
                        ) : <span className="schedule-calendar__empty-cell" aria-label="Showroom chưa mở lịch" />}
                      </div>
                    )
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>

        {!weekSlotCount && (
          <div className="schedule-calendar__empty">
            <CalendarBlank size={19} weight="light" />
            <span><strong>Showroom chưa mở lịch cho tuần này.</strong><small>Chuyển sang tuần khác hoặc nhắn ViVi ngày bạn mong muốn.</small></span>
          </div>
        )}
      </div>
    </section>
  )
}

/**
 * BookingNextSteps — hướng dẫn sau khi đặt lịch thành công.
 *
 * Rút về ĐÚNG BA việc người vừa đặt lịch cần làm (anh Minh chốt 17/08/2026):
 * mang giấy phép lái xe · xưng danh ở quầy lễ tân · có mặt sớm 15 phút.
 * Bản trước có bốn mục kèm địa chỉ, chỉ đường, tư vấn viên, hotline, lịch nhắc — những thứ đó
 * đã nằm nguyên trên phiếu lịch ở màn hình bên trái, lặp lại ở đây chỉ làm loãng.
 *
 * QUY TẮC NỘI DUNG giữ nguyên: mỗi dòng phải có nguồn dữ liệu thật, không bịa quy trình.
 * Tên người lái lấy từ form; giờ hẹn lấy từ `slot`. KHÔNG in mã lịch ở đây nữa — lễ tân tra
 * bằng tên, số điện thoại và email đã đăng ký, người dùng không phải nhớ mã.
 *
 * TODO [BACKEND/BOOKING]: chưa có API nào trả hạng GPLX yêu cầu cho mẫu xe
 * (`vehicle_models.required_license_class` có trong DB nhưng không xuất hiện ở
 * GET /vehicles/{id}), nên mục "Mang theo" chỉ nói "đúng hạng" chứ không nêu hạng cụ thể.
 */
/** Người dùng nên tới sớm chừng này để làm thủ tục và được nhân viên đón tiếp. */
const ARRIVE_EARLY_MINUTES = 15

export function BookingNextSteps({ slot, person, recipient }) {
  const driverName = recipient === 'other' ? person.driverName : person.bookingName
  const contactName = person.bookingName
  const contactPhone = person.phone
  const contactEmail = person.email

  return (
    <section className="booking-next-steps" aria-labelledby="booking-next-steps-title">
      <h2 id="booking-next-steps-title">Ba việc bạn cần lưu ý trước buổi lái thử</h2>

      <ol className="booking-next-steps__list">
        <li>
          <span className="booking-next-steps__label">Giấy tờ mang theo</span>
          <p>
            Bạn nhớ mang theo <strong>giấy phép lái xe</strong> còn hiệu lực và đúng hạng với mẫu xe
            đã đăng ký. Giấy phép cần mang tên <strong>{driverName || 'người lái thử'}</strong>,
            trùng với thông tin bạn vừa điền.
          </p>
        </li>

        <li>
          <span className="booking-next-steps__label">Khi tới quầy lễ tân</span>
          <p>
            Bạn chỉ cần đọc tên, số điện thoại và email đã đăng ký cho lễ tân là được. Bạn không cần
            nhớ mã lịch, vì showroom tra được bằng ba thông tin này.
          </p>
          <p className="booking-next-steps__muted">
            {[contactName, contactPhone, contactEmail].filter(Boolean).join(' · ')}
          </p>
        </li>

        <li>
          <span className="booking-next-steps__label">Thời gian có mặt</span>
          <p>
            Bạn nên có mặt trước giờ hẹn ít nhất <strong>{ARRIVE_EARLY_MINUTES} phút</strong> để
            làm thủ tục, và để nhân viên showroom có thời gian đón tiếp bạn chu đáo.
          </p>
          {slot?.time && slot?.dateLabel && (
            <p className="booking-next-steps__muted">
              Giờ hẹn của bạn là {slot.time}, {slot.dateLabel}.
            </p>
          )}
        </li>
      </ol>
    </section>
  )
}

export function BookingTicket({ car, showroom, slot, person, recipient, bookingCode, advisor = null, compact = false }) {
  const advisorLabel = advisor?.full_name
    ? `${advisor.full_name}${advisor.phone ? ` · ${advisor.phone}` : ''}`
    : bookingCode
      ? 'Chưa phân công'
      : 'Sẽ được phân công khi xác nhận'
  // Đặt hộ và người lái có liên hệ riêng: phiếu phải nói rõ AI nhận thông báo nào,
  // nếu không showroom sẽ gọi nhầm người đặt trong khi người cầm lái không hay biết.
  const bookingForOther = recipient === 'other'
  const driverHasOwnContact = bookingForOther && person.driverSameContact === false
  const contactLine = (phone, email) => [phone, email].filter(Boolean).join(' · ') || 'Chưa có thông tin liên hệ'

  const mapsUrl = (showroom.latitude && showroom.longitude)
    ? `https://www.google.com/maps/search/?api=1&query=${showroom.latitude},${showroom.longitude}`
    : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(showroom.name + ' ' + (showroom.address || ''))}`

  const showroomElement = (
    <a
      href={mapsUrl}
      target="_blank"
      rel="noopener noreferrer"
      style={{ color: '#0C64E6', textDecoration: 'underline', fontWeight: 600 }}
      title="Bấm để mở vị trí và chỉ đường trên Google Maps"
    >
      {showroom.name} ↗
    </a>
  )

  const rows = [
    ['Người đặt lịch', person.bookingName],
    ['Liên hệ người đặt', contactLine(person.phone, person.email)],
    ['Người lái thử', bookingForOther ? person.driverName : person.bookingName],
    ...(bookingForOther
      ? [['Liên hệ người lái', driverHasOwnContact
          ? contactLine(person.driverPhone, person.driverEmail)
          : 'Dùng chung liên hệ với người đặt']]
      : []),
    ['Mẫu xe', car.name],
    ['Showroom', showroomElement],
    ['Thời gian', `${slot.time} · ${slot.dateLabel}`],
    ['Tư vấn viên', advisorLabel],
  ]
  return <section className={`studio-ticket ${compact ? 'studio-ticket--compact' : ''}`}><header><span>{bookingCode ? 'Lịch lái thử đã xác nhận' : 'Kiểm tra trước khi đặt lịch'}</span>{bookingCode && <strong>{bookingCode}</strong>}</header><div className="studio-ticket__vehicle"><VehicleShot car={car} mode="cutout" /><span><strong>{car.name}</strong><small>{car.body}</small></span></div><dl>{rows.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl><p><CheckCircle size={16} weight="fill" /> Đã xác nhận có giấy phép lái xe phù hợp.</p></section>
}
