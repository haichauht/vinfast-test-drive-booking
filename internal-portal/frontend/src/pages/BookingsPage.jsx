import { CaretDown, Check, CircleNotch, ClockCounterClockwise, EnvelopeSimple, Funnel, IdentificationCard, Phone, SignIn, Sparkle, UserFocus, UserMinus, X } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { PageState } from '../components/PageState.jsx'
import { StatusBadge } from '../components/StatusBadge.jsx'
import { useRemote } from '../hooks.js'
import { formatDateTime } from '../utils.js'

const statuses = ['', 'held', 'confirmed', 'checked_in', 'completed', 'no_show', 'cancelled', 'rescheduled']
const channelLabels = { zalo: 'Zalo', sms: 'SMS', email: 'Email' }

function CustomerProfile({ profile, customerNote }) {
  if (!profile) return <div className="customer-profile__empty">Booking này chưa có đủ thông tin để tạo hồ sơ khách hàng.</div>
  const summary = profile.summary || {}
  const license = profile.license || {}
  const preferredChannel = channelLabels[profile.preferred_channel] || profile.preferred_channel || 'Chưa chọn'
  const initials = (profile.full_name || '?').split(/\s+/).filter(Boolean).slice(-2).map((part) => part[0]).join('').toUpperCase()

  return (
    <section className="customer-profile" aria-label="Hồ sơ khách hàng">
      <div className="customer-profile__identity">
        <span className="customer-profile__avatar">{initials}</span>
        <div>
          <strong>{profile.full_name || 'Khách hàng chưa cập nhật tên'}</strong>
          <small>{summary.total_bookings > 1 ? 'Khách quay lại' : 'Hồ sơ khách mới'} · Ưu tiên {preferredChannel}</small>
        </div>
      </div>
      <div className="customer-profile__contacts">
        <a href={profile.phone ? `tel:${profile.phone}` : undefined} aria-disabled={!profile.phone}><Phone size={16} />{profile.phone || 'Chưa có số điện thoại'}</a>
        <a href={profile.email ? `mailto:${profile.email}` : undefined} aria-disabled={!profile.email}><EnvelopeSimple size={16} />{profile.email || 'Chưa có email'}</a>
      </div>
      <div className="customer-profile__metrics">
        <div><strong>{summary.total_bookings || 0}</strong><span>Tổng booking</span></div>
        <div><strong>{summary.completed_bookings || 0}</strong><span>Đã hoàn tất</span></div>
        <div><strong>{(summary.cancelled_bookings || 0) + (summary.no_show_bookings || 0)}</strong><span>Hủy / no-show</span></div>
      </div>
      <div className="customer-profile__context">
        <span className="section-label">Thông tin giúp sale chuẩn bị</span>
        <ul>
          <li>Kênh liên hệ khách ưu tiên: <strong>{preferredChannel}</strong>.</li>
          <li>Mẫu xe từng quan tâm: <strong>{profile.vehicle_interests?.map((item) => item.model).join(', ') || 'Chưa có dữ liệu'}</strong>.</li>
          <li>GPLX đã khai báo: <strong>{license.declared_license_class || 'Chưa khai báo'}</strong> · trạng thái <strong>{license.check_status || 'Chưa kiểm tra'}</strong>.</li>
          {customerNote && <li>Ghi chú khách hàng: <strong>{customerNote}</strong>.</li>}
          {!profile.booker_is_driver && profile.booker && <li>Người đặt hộ: <strong>{profile.booker.full_name || 'Chưa cập nhật'}</strong>{profile.booker.phone ? ` · ${profile.booker.phone}` : ''}.</li>}
        </ul>
      </div>
      <div className="customer-profile__history">
        <div className="customer-profile__history-title"><span className="section-label">Lịch sử booking được phép xem</span><ClockCounterClockwise size={17} /></div>
        {(profile.history || []).map((item) => (
          <div className="customer-profile__history-row" key={item.id}>
            <div><strong>{item.vehicle_model} · {item.vehicle_variant}</strong><small>{item.showroom_name} · {formatDateTime(item.start_at)}</small></div>
            <StatusBadge status={item.status} />
          </div>
        ))}
        {!profile.history?.length && <p>Chưa có booking đã xác nhận trong phạm vi của bạn.</p>}
      </div>
    </section>
  )
}

function ProfileSummary({ markdown }) {
  const lines = markdown.split(/\r?\n/)
  const blocks = []
  let listItems = []

  const flushList = () => {
    if (!listItems.length) return
    blocks.push(<ul key={`list-${blocks.length}`}>{listItems}</ul>)
    listItems = []
  }
  const formatInline = (text) => text.split(/(\*\*[^*]+\*\*)/g).map((part, index) => (
    part.startsWith('**') && part.endsWith('**')
      ? <strong key={index}>{part.slice(2, -2)}</strong>
      : part
  ))

  lines.forEach((line, index) => {
    const trimmed = line.trim()
    if (!trimmed) {
      flushList()
      return
    }
    const heading = trimmed.match(/^(#{1,3})\s+(.+)$/)
    const listItem = trimmed.match(/^[-*]\s+(.+)$/)
    if (heading) {
      flushList()
      const Tag = `h${heading[1].length}`
      blocks.push(<Tag key={`heading-${index}`}>{formatInline(heading[2])}</Tag>)
    } else if (listItem) {
      listItems.push(<li key={`item-${index}`}>{formatInline(listItem[1])}</li>)
    } else {
      flushList()
      blocks.push(<p key={`text-${index}`}>{formatInline(trimmed)}</p>)
    }
  })
  flushList()
  return <div className="profile-summary__content">{blocks}</div>
}

export function BookingsPage({ token, user }) {
  const canManage = user.role !== 'staff'
  const [status, setStatus] = useState('')
  const [date, setDate] = useState('')
  const [showroom, setShowroom] = useState(user.role === 'showroom_manager' ? user.showroom_ids?.[0] || '' : '')
  const [staffId, setStaffId] = useState('')
  const [vehicleId, setVehicleId] = useState('')
  const [selected, setSelected] = useState(null)
  const [assignment, setAssignment] = useState('')
  const [notice, setNotice] = useState('')
  const [actionError, setActionError] = useState('')
  const [busy, setBusy] = useState(false)
  const [profileSummary, setProfileSummary] = useState('')
  const [profileSummaryMeta, setProfileSummaryMeta] = useState(null)
  const [profileSummaryError, setProfileSummaryError] = useState('')
  const [profileSummaryLoading, setProfileSummaryLoading] = useState(false)
  const canViewProfileSummary = selected && ['confirmed', 'cancelled'].includes(selected.status)
  const [profileOpen, setProfileOpen] = useState(false)
  const [profileLoading, setProfileLoading] = useState(false)
  const [profileError, setProfileError] = useState('')
  const bookingState = useRemote(
    () => api.bookings(token, {
      status,
      date,
      showroom_id: showroom,
      staff_id: canManage ? staffId : '',
      vehicle_id: canManage ? vehicleId : '',
      limit: 100,
    }),
    [token, status, date, showroom, staffId, vehicleId, canManage],
  )
  const showroomState = useRemote(() => api.showrooms(token), [token])
  const staffState = useRemote(
    () => (canManage ? api.staff(token, showroom) : Promise.resolve([])),
    [token, showroom, canManage],
  )
  const vehicleState = useRemote(
    () => (canManage ? api.vehicles(token, { showroom_id: showroom }) : Promise.resolve([])),
    [token, showroom, canManage],
  )

  useEffect(() => {
    if (selected && bookingState.data?.items) {
      const refreshed = bookingState.data.items.find((item) => item.id === selected.id) || null
      setSelected((current) => refreshed ? { ...current, ...refreshed } : null)
      setAssignment(refreshed?.assigned_staff_id || '')
    }
  }, [bookingState.data])

  const openBooking = (booking) => {
    setSelected(booking)
    setAssignment(booking.assigned_staff_id || '')
    setNotice('')
    setActionError('')
    setProfileOpen(false)
    setProfileLoading(false)
    setProfileError('')
    setProfileSummary('')
    setProfileSummaryMeta(null)
    setProfileSummaryError('')
  }

  const toggleCustomerProfile = async () => {
    if (profileOpen) {
      setProfileOpen(false)
      return
    }
    if (selected.customer_profile !== undefined) {
      setProfileOpen(true)
      return
    }
    const bookingId = selected.id
    setProfileLoading(true)
    setProfileError('')
    try {
      const detail = await api.booking(token, bookingId)
      setSelected((current) => current?.id === bookingId ? { ...current, ...detail } : current)
      setProfileOpen(true)
    } catch (error) {
      setProfileError(error.message)
    } finally {
      setProfileLoading(false)
    }
  }

  const run = async (operation, successMessage) => {
    setActionError('')
    setNotice('')
    setBusy(true)
    try {
      await operation()
      setNotice(successMessage)
      await bookingState.reload()
    } catch (error) {
      setActionError(error.message)
    } finally {
      setBusy(false)
    }
  }

  const assign = () => run(
    () => api.assignBooking(token, selected.id, assignment),
    'Đã cập nhật nhân viên phụ trách và ghi nhật ký vận hành.',
  )

  const verifyLicense = () => run(
    () => api.checkLicense(token, selected.id, {
      ui_action_id: `portal-license-${crypto.randomUUID()}`,
      original_document_presented: true,
      license_class_matches: true,
      is_currently_valid: true,
      result: 'verified',
    }),
    'Đã xác minh giấy phép lái xe.',
  )

  const rejectLicense = () => {
    const reason = window.prompt('Nhập lý do từ chối giấy phép lái xe:')
    if (!reason?.trim()) return
    run(
      () => api.checkLicense(token, selected.id, {
        ui_action_id: `portal-license-${crypto.randomUUID()}`,
        original_document_presented: false,
        license_class_matches: false,
        is_currently_valid: false,
        result: 'rejected',
        rejection_reason: reason.trim(),
      }),
      'Đã ghi nhận giấy phép không hợp lệ.',
    )
  }

  const transition = (target, label, dangerous = false) => {
    if (dangerous && !window.confirm(`Xác nhận ${label.toLowerCase()} booking ${selected.booking_code}?`)) return
    run(
      () => api.transitionBooking(token, selected.id, target, `Thực hiện bởi ${user.display_name}`),
      `Đã ${label.toLowerCase()} booking.`,
    )
  }

  const loadProfileSummary = async ({ refresh = false } = {}) => {
    if (!selected || profileSummaryLoading) return
    setProfileSummaryLoading(true)
    setProfileSummaryError('')
    try {
      const result = await api.profileSummary(token, selected.id, { refresh })
      setProfileSummary(result.text)
      setProfileSummaryMeta(result)
    } catch (error) {
      setProfileSummaryError(error.message)
    } finally {
      setProfileSummaryLoading(false)
    }
  }

  const clearFilters = () => {
    setStatus('')
    setDate('')
    setStaffId('')
    setVehicleId('')
    if (user.role === 'operations_admin') setShowroom('')
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h2>{user.role === 'staff' ? 'Booking được phân công cho tôi' : 'Quản lý booking lái thử'}</h2>
          <p>{bookingState.data?.total || 0} booking trong phạm vi được backend cho phép.</p>
        </div>
      </div>
      <div className="filter-bar">
        <Funnel size={20} />
        <select value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">Tất cả trạng thái</option>
          {statuses.slice(1).map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
        {user.role === 'operations_admin' && (
          <select value={showroom} onChange={(event) => { setShowroom(event.target.value); setStaffId(''); setVehicleId('') }}>
            <option value="">Tất cả showroom</option>
            {(showroomState.data || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        )}
        <input type="date" value={date} onChange={(event) => setDate(event.target.value)} />
        {canManage && (
          <>
            <select value={staffId} onChange={(event) => setStaffId(event.target.value)}>
              <option value="">Tất cả nhân viên</option>
              {(staffState.data || []).map((item) => <option key={item.id} value={item.id}>{item.full_name}</option>)}
            </select>
            <select value={vehicleId} onChange={(event) => setVehicleId(event.target.value)}>
              <option value="">Tất cả xe demo</option>
              {(vehicleState.data || []).map((item) => <option key={item.id} value={item.id}>{item.asset_code}</option>)}
            </select>
          </>
        )}
        {(status || date || staffId || vehicleId || (showroom && user.role === 'operations_admin')) && (
          <button className="text-button" onClick={clearFilters}>Xóa bộ lọc</button>
        )}
      </div>
      <PageState loading={bookingState.loading} error={bookingState.error}>
        <div className="table-card">
          <div className="data-table data-table--bookings">
            <div className="data-table__head"><span>Mã lịch</span><span>Khách hàng</span><span>Xe & showroom</span><span>Thời gian</span><span>Trạng thái</span></div>
            {(bookingState.data?.items || []).map((booking) => (
              <button className="data-table__row" key={booking.id} onClick={() => openBooking(booking)}>
                <span><strong>{booking.booking_code || 'Draft'}</strong><small>{booking.assigned_staff_name || 'Chưa phân công'}</small></span>
                <span><strong>{booking.driver_name || 'Chưa cập nhật'}</strong><small>{booking.driver_phone || booking.booker_phone || '—'}</small></span>
                <span><strong>{booking.vehicle_model} · {booking.vehicle_variant}</strong><small>{booking.showroom_name}</small></span>
                <span><strong>{formatDateTime(booking.start_at)}</strong><small>{booking.asset_code}</small></span>
                <span><StatusBadge status={booking.status} /></span>
              </button>
            ))}
          </div>
          {!bookingState.data?.items?.length && <div className="empty-state">Không có booking phù hợp bộ lọc.</div>}
        </div>
      </PageState>
      {selected && (
        <div className="drawer-layer">
          <button className="drawer-backdrop" onClick={() => setSelected(null)} aria-label="Đóng chi tiết" />
          <aside className="drawer booking-detail-modal" role="dialog" aria-modal="true" aria-label="Chi tiết booking">
            <div className="drawer__header"><div><span className="eyebrow">Chi tiết booking</span><h3>{selected.booking_code || 'Booking draft'}</h3></div><button className="icon-button" onClick={() => setSelected(null)}><X size={20} /></button></div>
            <div className="drawer__status"><StatusBadge status={selected.status} /><span>Version {selected.version}</span></div>
            <button className={`customer-profile-trigger ${profileOpen ? 'customer-profile-trigger--open' : ''}`} onClick={toggleCustomerProfile} disabled={profileLoading} aria-expanded={profileOpen}>
              <span className="customer-profile-trigger__icon"><UserFocus size={21} /></span>
              <span><strong>{profileLoading ? 'Đang tải hồ sơ...' : 'Xem hồ sơ khách hàng'}</strong><small>Thông tin liên hệ, lịch sử và sở thích xe</small></span>
              <CaretDown className="customer-profile-trigger__caret" size={18} />
            </button>
            {profileError && <div className="form-error customer-profile-error">{profileError}</div>}
            {profileOpen && <CustomerProfile profile={selected.customer_profile} customerNote={selected.customer_note} />}
            <dl className="detail-list">
              <div><dt>Người lái</dt><dd>{selected.driver_name || 'Chưa cập nhật'}<small>{selected.driver_phone || selected.booker_phone || 'Không có số liên hệ'} · {selected.driver_email || selected.booker_email || 'Không có email'}</small></dd></div>
              <div><dt>Xe demo</dt><dd>{selected.vehicle_model} · {selected.vehicle_variant}<small>{selected.asset_code} · {selected.plate_number || 'Chưa có biển số'} · {selected.vehicle_operational_status} · pin {selected.vehicle_battery_soc ?? '—'}%</small></dd></div>
              <div><dt>Showroom</dt><dd>{selected.showroom_name}</dd></div>
              <div><dt>Thời gian</dt><dd>{formatDateTime(selected.start_at)}<small>Đến {formatDateTime(selected.end_at)}</small></dd></div>
              <div><dt>Phụ trách</dt><dd>{selected.assigned_staff_name || 'Chưa phân công'}</dd></div>
              <div><dt>GPLX</dt><dd>{selected.license_check_status || 'Chưa khai báo'}</dd></div>
              <div><dt>Ghi chú</dt><dd>{selected.customer_note || 'Không có ghi chú khách hàng'}<small>{selected.internal_note || 'Không có ghi chú nội bộ'}</small></dd></div>
            </dl>
            {canViewProfileSummary && <section className="profile-summary" aria-live="polite">
              <div className="profile-summary__header">
                <div>
                  <span className="section-label">Hồ sơ khách hàng</span>
                  <p>Tóm tắt nhu cầu và các điểm cần lưu ý trước buổi lái thử.</p>
                </div>
                <button className="secondary-button" disabled={profileSummaryLoading} onClick={() => loadProfileSummary({ refresh: Boolean(profileSummary) })}>
                  {profileSummaryLoading ? <CircleNotch className="spin" size={18} /> : <Sparkle size={18} />}
                  {profileSummaryLoading ? 'Đang tổng hợp…' : profileSummary ? 'Cập nhật tóm tắt' : 'Xem tóm tắt'}
                </button>
              </div>
              {profileSummaryLoading && <div className="profile-summary__loading"><CircleNotch className="spin" size={18} />Yêu cầu đã được nhận, hệ thống đang tổng hợp hồ sơ khách hàng. Việc này có thể mất vài giây.</div>}
              {profileSummaryError && <div className="form-error">{profileSummaryError}</div>}
              {profileSummary && !profileSummaryLoading && <><div className="profile-summary__meta">{profileSummaryMeta?.source === 'cache' ? 'Đang hiển thị bản đã lưu' : 'Đã cập nhật bản tóm tắt mới nhất'}{profileSummaryMeta?.generatedAt ? ` · ${new Intl.DateTimeFormat('vi-VN', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(profileSummaryMeta.generatedAt))}` : ''}</div><ProfileSummary markdown={profileSummary} /></>}
            </section>}
            {!canViewProfileSummary && <div className="read-only-note">Hồ sơ khách hàng chỉ khả dụng sau khi booking đã xác nhận, hoặc với booking đã xác nhận nhưng sau đó bị hủy.</div>}
            {user.role === 'staff' && <div className="read-only-note">Tài khoản Staff chỉ có quyền xem. Mọi thay đổi do quản lý showroom thực hiện.</div>}
            {notice && <div className="form-success"><Check size={18} />{notice}</div>}
            {actionError && <div className="form-error">{actionError}</div>}
            {canManage && (
              <div className="drawer__actions">
                <span className="section-label">Phân công nhân viên</span>
                <div className="inline-action">
                  <select value={assignment} onChange={(event) => setAssignment(event.target.value)}>
                    <option value="">Chọn nhân viên</option>
                    {(staffState.data || []).map((item) => <option key={item.id} value={item.id}>{item.full_name}</option>)}
                  </select>
                  <button className="secondary-button" disabled={!assignment || busy} onClick={assign}>Phân công</button>
                </div>
                <span className="section-label">Thao tác nghiệp vụ</span>
                {selected.status === 'confirmed' && selected.license_check_status !== 'verified' && (
                  <div className="inline-action">
                    <button className="secondary-button" disabled={busy || !selected.assigned_staff_id} onClick={verifyLicense}><IdentificationCard size={19} />Xác minh GPLX</button>
                    <button className="danger-button" disabled={busy || !selected.assigned_staff_id} onClick={rejectLicense}>Từ chối GPLX</button>
                  </div>
                )}
                {selected.status === 'confirmed' && selected.license_check_status === 'verified' && <button className="primary-button" disabled={busy} onClick={() => transition('checked_in', 'Check-in')}><SignIn size={19} />Check-in khách</button>}
                {selected.status === 'checked_in' && <button className="primary-button" disabled={busy} onClick={() => transition('completed', 'Hoàn tất')}><Check size={19} />Hoàn tất lái thử</button>}
                {selected.status === 'confirmed' && <button className="danger-button" disabled={busy} onClick={() => transition('no_show', 'Đánh dấu no-show', true)}><UserMinus size={19} />Đánh dấu no-show</button>}
                {selected.status === 'confirmed' && <button className="danger-button" disabled={busy} onClick={() => transition('cancelled', 'Hủy', true)}><X size={19} />Hủy booking</button>}
              </div>
            )}
          </aside>
        </div>
      )}
    </>
  )
}
