import { useEffect } from 'react'
import { ArrowRight, CaretDown, Check, X } from '@phosphor-icons/react'
import { Link } from 'react-router-dom'
import { SmartImage } from '../SmartImage'
import { carGroups } from '../../data/cars'

export function VehicleShot({ car, className = '', eager = false }) {
  return <SmartImage className={`vehicle-shot vehicle-shot--${car.studioShot.mode} ${className}`.trim()} src={car.studioShot.src} alt={`${car.name} — ảnh studio`} eager={eager} />
}

export function VehicleSwitcher({ cars, currentId, onSelect, onClose }) {
  useEffect(() => { const close = (event) => event.key === 'Escape' && onClose(); window.addEventListener('keydown', close); return () => window.removeEventListener('keydown', close) }, [onClose])
  return <div className="vehicle-switcher" role="dialog" aria-modal="true" aria-labelledby="vehicle-switcher-title" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><div className="vehicle-switcher__panel">
    <button type="button" className="vehicle-switcher__close" onClick={onClose} aria-label="Đóng bảng chọn xe"><X size={17} weight="light" /></button>
    <header><p>Đổi mẫu xe lái thử</p><h2 id="vehicle-switcher-title">Bạn muốn cầm lái mẫu nào?</h2><small>ViVi giữ lại địa chỉ và showroom bạn đã chọn; chỉ khung giờ được mở lại để ghép đúng xe mới.</small></header>
    <div className="vehicle-switcher__body">{carGroups.map((group) => <section key={group.id}><div className="vehicle-switcher__group"><strong>{group.label}</strong><small>{group.description}</small></div><div className="vehicle-switcher__grid">{cars.filter((car) => car.category === group.id).map((car) => { const active = car.id === currentId; return <button type="button" key={car.id} className={active ? 'is-active' : ''} onClick={() => onSelect(car)} aria-pressed={active}><VehicleShot car={car} className="vehicle-switcher__shot" /><span className="vehicle-switcher__meta"><strong>{car.name}</strong><small>{car.body} · {car.seats}</small></span><span className="vehicle-switcher__state">{active ? <><Check size={13} weight="bold" /> Đang chọn</> : <>Chọn mẫu này <ArrowRight size={13} weight="light" /></>}</span></button> })}</div></section>)}</div>
  </div></div>
}

export function VehiclePanel({ car }) {
  return <section className="studio-vehicle" aria-label={`Mẫu xe ${car.name}`}><div className="studio-vehicle__ambient" aria-hidden="true" /><div className="studio-vehicle__heading"><span>Mẫu xe đang giữ</span><strong>{car.name}</strong><small>{car.body} · {car.seats}</small></div><div className="studio-vehicle__stage" key={car.id}><VehicleShot car={car} className="studio-vehicle__image" eager /></div><div className="studio-vehicle__specs">{car.specs.slice(0, 3).map((spec) => <div key={spec.label}><strong>{spec.value}</strong><span>{spec.label}</span></div>)}</div><Link to={`/models/${car.id}`}>Xem lại thông tin xe <ArrowRight size={15} weight="light" /></Link></section>
}
