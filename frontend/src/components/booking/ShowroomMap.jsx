/**
 * components/booking/ShowroomMap.jsx — Bản đồ chọn showroom (bước 3 của luồng đặt lịch).
 *
 * ✅ ĐANG DÙNG THẬT: BookingPage.jsx import dưới tên BookingShowroomMap và render khi tab = 'map'.
 * (BookingPage.jsx còn một bản ShowroomMap cũ ở dòng ~446 nhưng bản đó KHÔNG được render nữa.)
 *
 * Bố cục: danh sách showroom bên trái · bản đồ bên phải · thẻ xem trước + nút "Xem lịch" nổi dưới.
 *
 * Bản đồ dùng gì:
 * - Thư viện Leaflet 1.9.4 tải TỪ CDN unpkg.com lúc chạy (không nằm trong package.json)
 *   → mất mạng thì bản đồ không hiện, dù phần còn lại của web vẫn chạy.
 * - Ô bản đồ (tile) lấy từ Google Maps. Chưa có API key nên chưa dùng được cho production.
 * - LƯU Ý: package.json có cài mapbox-gl nhưng file này KHÔNG dùng tới.
 * - Marker showroom là logo VinFast, marker vị trí người dùng là chấm tròn — cả hai vẽ bằng
 *   L.divIcon với class .leaflet-showroom-marker / .leaflet-user-marker (style ở cuối index.css).
 *
 * Khoảng cách "km" chỉ hiện khi backend trả về, không tự bịa số 0.
 * Sửa ở đây khi: đổi bố cục danh sách/bản đồ, đổi icon marker, đổi mức zoom (đang 11 và 14).
 */
import { useEffect, useRef, useState } from 'react'
import { Crosshair, Minus, Plus } from '@phosphor-icons/react'
import { commonMedia } from '../../media/assets'

const vinfastLogo = commonMedia.vinfastLogo

export function ShowroomMap({ car, showrooms, selectedId, onSelect, onConfirm, userLocation }) {
  const mapContainerRef = useRef(null)
  const mapRef = useRef(null)
  const markersRef = useRef([])
  const userMarkerRef = useRef(null)
  const [leafletLoaded, setLeafletLoaded] = useState(false)
  const selected = showrooms.find((showroom) => showroom.id === selectedId) || null
  const hasLocation = !!userLocation || showrooms.some((showroom) => showroom.distance > 0)

  useEffect(() => {
    if (window.L) { setLeafletLoaded(true); return }
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
    document.head.appendChild(link)
    const script = document.createElement('script')
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
    script.async = true
    script.onload = () => setLeafletLoaded(true)
    document.body.appendChild(script)
  }, [])

  useEffect(() => {
    if (!leafletLoaded || !mapContainerRef.current) return
    const initialCenter = selected ? [selected.latitude, selected.longitude] : userLocation ? [userLocation.latitude, userLocation.longitude] : [21.028511, 105.804817]
    const map = window.L.map(mapContainerRef.current, { zoomControl: false }).setView(initialCenter, selected ? 14 : 11)
    window.L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', { attribution: '&copy; Google Maps' }).addTo(map)
    mapRef.current = map
    return () => { map.remove(); mapRef.current = null }
  }, [leafletLoaded])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !leafletLoaded) return
    const L = window.L
    markersRef.current.forEach((marker) => marker.remove())
    markersRef.current = showrooms.map((showroom) => {
      const active = selectedId === showroom.id ? ' is-active' : ''
      const icon = L.divIcon({ html: `<div class="leaflet-showroom-marker${active}"><img src="${vinfastLogo}" alt="VinFast" /></div>`, className: '', iconSize: [32, 32], iconAnchor: [16, 16], popupAnchor: [0, -16] })
      const marker = L.marker([showroom.latitude, showroom.longitude], { icon }).bindPopup(`<strong>${showroom.name}</strong><br/><small>${showroom.address}</small>`).addTo(map)
      marker.on('click', () => onSelect(showroom.id))
      return marker
    })
  }, [showrooms, selectedId, onSelect, leafletLoaded])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !userLocation || !leafletLoaded) return
    userMarkerRef.current?.remove()
    const icon = window.L.divIcon({ html: '<div class="leaflet-user-marker"></div>', className: '', iconSize: [18, 18], iconAnchor: [9, 9] })
    userMarkerRef.current = window.L.marker([userLocation.latitude, userLocation.longitude], { icon }).addTo(map)
  }, [userLocation, leafletLoaded])

  useEffect(() => {
    if (mapRef.current && selected && leafletLoaded) mapRef.current.setView([selected.latitude, selected.longitude], 14, { animate: true, duration: 1 })
  }, [selectedId, leafletLoaded])

  const centerUser = () => userLocation && mapRef.current?.setView([userLocation.latitude, userLocation.longitude], 14, { animate: true })

  return (
    <section className="studio-map studio-map--familiar" aria-label="Bản đồ showroom phù hợp">
      <aside className="studio-map__list">
        <div className="studio-map__intro"><span>{showrooms.length} showroom có {car.name}</span><small>Ưu tiên có đúng xe, sau đó mới tính khoảng cách</small></div>
        {showrooms.map((showroom, index) => (
          <button type="button" key={showroom.id} className={selectedId === showroom.id ? 'is-active' : ''} onClick={() => onSelect(showroom.id)}>
            <span>{index + 1}</span><span><strong>{showroom.name}</strong><small>{showroom.address}</small></span>{hasLocation && <em>{String(showroom.distance).replace('.', ',')} km</em>}
          </button>
        ))}
      </aside>
      <div className="studio-map__canvas">
        <div ref={mapContainerRef} className="studio-map__leaflet-container" />
        <div className="studio-map__controls" aria-label="Điều khiển bản đồ">
          <button type="button" onClick={() => mapRef.current?.zoomIn()} aria-label="Phóng to"><Plus size={17} weight="regular" /></button>
          <button type="button" onClick={() => mapRef.current?.zoomOut()} aria-label="Thu nhỏ"><Minus size={17} weight="regular" /></button>
          <button type="button" onClick={centerUser} disabled={!userLocation} aria-label="Vị trí của tôi"><Crosshair size={17} weight="regular" /></button>
        </div>
        {selected && <div className="studio-map__preview"><span><strong>{selected.name}</strong><small>{selected.address}{selected.phone ? ` · SĐT: ${selected.phone}` : ''}{hasLocation && selected.distance !== undefined && selected.distance !== null ? ` · Cách bạn ${String(selected.distance).replace('.', ',')} km` : ''}</small></span><button type="button" onClick={() => onConfirm(selected)} className="studio-map__preview-confirm">Xem lịch</button></div>}
      </div>
    </section>
  )
}
