import { useEffect, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { ArrowUpRight, Buildings, CaretDown, CarProfile } from '@phosphor-icons/react'
import { Brand } from './Brand'
import { IslandButton } from './IslandButton'

const links = [
  { label: 'Công nghệ', to: '/#technology' },
  { label: 'Hệ sinh thái', to: '/#ecosystem' },
  { label: 'ViVi đặt lịch', to: '/booking' },
]

const productGroups = [
  { label: 'Động cơ điện', copy: 'Dải xe cá nhân từ VF 3 đến VF 9.', to: '/#models-electric', icon: CarProfile },
  { label: 'Dòng xe dịch vụ', copy: 'Green, giao vận và vận tải công cộng.', to: '/#models-service', icon: Buildings },
]

export function AppShell({ children, navTheme = 'light' }) {
  const [menuOpen, setMenuOpen] = useState(false)
  const [productsOpen, setProductsOpen] = useState(false)
  const [bookingHref, setBookingHref] = useState('/booking')
  const location = useLocation()

  useEffect(() => {
    // TODO [BACKEND/SESSION]: Today this context is anonymous and tab-scoped.
    // When draft persistence exists, restore `recentVehicleId` from
    // GET /api/v1/test-drive/drafts/{draftId}; sessionStorage remains a safe
    // fallback only for the non-PII vehicle id. Never persist customer fields here.
    setMenuOpen(false)
    setProductsOpen(false)
    const routeCar = location.pathname.match(/^\/cars\/([^/]+)/)?.[1]
    const recentCar = routeCar || window.sessionStorage.getItem('vinfast:last-viewed-car')
    setBookingHref(recentCar ? `/booking?car=${recentCar}` : '/booking')
  }, [location.pathname, location.hash])

  useEffect(() => {
    if (!menuOpen) return undefined
    const onKeyDown = (event) => {
      if (event.key === 'Escape') setMenuOpen(false)
    }
    document.addEventListener('keydown', onKeyDown)
    document.body.classList.add('menu-is-open')
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.classList.remove('menu-is-open')
    }
  }, [menuOpen])

  useEffect(() => {
    if (!productsOpen) return undefined
    const closeProducts = (event) => {
      if (event.type === 'keydown' && event.key !== 'Escape') return
      if (event.type === 'pointerdown' && event.target.closest?.('.site-nav__products')) return
      setProductsOpen(false)
    }
    document.addEventListener('keydown', closeProducts)
    document.addEventListener('pointerdown', closeProducts)
    return () => {
      document.removeEventListener('keydown', closeProducts)
      document.removeEventListener('pointerdown', closeProducts)
    }
  }, [productsOpen])

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Đi đến nội dung chính
      </a>

      <header className={`site-nav site-nav--${navTheme}`}>
        <div className="site-nav__inner">
          <Brand inverse={navTheme === 'dark'} />

          <nav className="site-nav__links" aria-label="Điều hướng chính">
            <div className={`site-nav__products ${productsOpen ? 'is-open' : ''}`}>
              <button
                type="button"
                aria-expanded={productsOpen}
                aria-controls="vehicle-categories"
                onClick={() => setProductsOpen((open) => !open)}
              >
                Ô tô <CaretDown size={14} weight="light" />
              </button>
              <div id="vehicle-categories" className="vehicle-mega" aria-hidden={!productsOpen}>
                <div className="vehicle-mega__intro">
                  <span>Chọn cách bạn sử dụng xe</span>
                  <strong>Một catalogue, hai dòng sản phẩm rõ ràng.</strong>
                </div>
                <div className="vehicle-mega__links">
                  {productGroups.map(({ label, copy, to, icon: Icon }) => (
                    <a href={to} key={label} onClick={() => setProductsOpen(false)}>
                      <Icon size={24} weight="light" />
                      <span><strong>{label}</strong><small>{copy}</small></span>
                      <ArrowUpRight size={17} weight="light" />
                    </a>
                  ))}
                </div>
              </div>
            </div>
            {links.map((link) => (
              <a key={link.label} href={link.to}>
                {link.label}
              </a>
            ))}
          </nav>

          <div className="site-nav__actions">
            <IslandButton to={bookingHref} variant="blue" className="site-nav__booking">
              Đặt lịch lái thử
            </IslandButton>
            <button
              className={`menu-toggle ${menuOpen ? 'is-open' : ''}`}
              type="button"
              aria-label={menuOpen ? 'Đóng trình đơn' : 'Mở trình đơn'}
              aria-expanded={menuOpen}
              aria-controls="mobile-navigation"
              onClick={() => setMenuOpen((open) => !open)}
            >
              <span />
              <span />
            </button>
          </div>
        </div>
      </header>

      <div
        id="mobile-navigation"
        className={`menu-overlay ${menuOpen ? 'is-open' : ''}`}
        aria-hidden={!menuOpen}
      >
        <div className="menu-overlay__inner">
          <p className="menu-overlay__intro">Khám phá VinFast</p>
          <nav aria-label="Điều hướng di động">
            {productGroups.map(({ label, to }, index) => (
              <a
                href={to}
                key={label}
                style={{ '--menu-index': index }}
                tabIndex={menuOpen ? 0 : -1}
              >
                <span>Ô tô · {label}</span>
                <ArrowUpRight size={26} weight="light" />
              </a>
            ))}
            {links.map((link, index) => (
              <a
                href={link.to}
                key={link.label}
                style={{ '--menu-index': index + productGroups.length }}
                tabIndex={menuOpen ? 0 : -1}
              >
                <span>{link.label}</span>
                <ArrowUpRight size={26} weight="light" />
              </a>
            ))}
            <NavLink
              to={bookingHref}
              style={{ '--menu-index': links.length + productGroups.length }}
              tabIndex={menuOpen ? 0 : -1}
            >
              <span>Đặt lịch lái thử</span>
              <ArrowUpRight size={26} weight="light" />
            </NavLink>
          </nav>
          <div className="menu-overlay__foot">
            <span>VinFast Vietnam</span>
            <span>Thuần điện. Thuần Việt.</span>
          </div>
        </div>
      </div>

      {children}
    </div>
  )
}
