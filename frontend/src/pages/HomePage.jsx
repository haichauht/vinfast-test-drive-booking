import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useGSAP } from '@gsap/react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import {
  ArrowLeft,
  ArrowRight,
  BatteryCharging,
  MapPin,
  ShieldCheck,
} from '@phosphor-icons/react'
import { AppShell } from '../components/AppShell'
import { IslandButton } from '../components/IslandButton'
import { Reveal } from '../components/Reveal'
import { SmartImage } from '../components/SmartImage'
import { prefetchVehicle } from '../api/vehicles'
import { carGroups, carImage } from '../data/cars'
import { usePageContent, useVehicleCatalog } from '../hooks/useSiteData'
import {
  factoryAerial,
  factoryFilm,
  roadBanner,
  vf9Sculpture,
  viviPortrait,
} from '../data/media'

gsap.registerPlugin(useGSAP, ScrollTrigger)

function VehicleRail({ vehicles }) {
  const rail = useRef(null)

  const move = (direction) => {
    rail.current?.scrollBy({ left: direction * rail.current.clientWidth * 0.72, behavior: 'smooth' })
  }

  if (!vehicles.length) {
    return (
      <div className="vehicle-empty">
        <p>Chưa có mẫu xe trong nhóm này.</p>
        <span>Bạn hãy chọn nhóm còn lại để xem các mẫu đang mở bán.</span>
      </div>
    )
  }

  return (
    <>
      <div className="vehicle-rail" ref={rail}>
        {vehicles.map((car, index) => (
          <Link
            className="vehicle-tile"
            to={`/booking?car=${car.id}`}
            key={car.id}
            onMouseEnter={() => prefetchVehicle(car.id)}
            onFocus={() => prefetchVehicle(car.id)}
          >
            <span className="vehicle-tile__shell">
              <span className="vehicle-tile__core">
                <span className="vehicle-tile__meta">
                  <span>{car.body}</span>
                  <span>{car.seats}</span>
                </span>
                {/* Luôn dùng ảnh studio của mẫu xe để cả dải sản phẩm cùng một ngôn ngữ hình ảnh. */}
                <SmartImage
                  className={`vehicle-tile__image vehicle-shot vehicle-shot--${car.studioShot.mode}`}
                  src={car.studioShot.src}
                  alt={`${car.name} - ${car.body}`}
                  fit={car.studioShot.fit}
                  focalPoint={car.studioShot.focalPoint}
                  aspectRatio={car.studioShot.aspectRatio}
                />
                <span className="vehicle-tile__copy">
                  <span>
                    <strong>{car.name}</strong>
                    <small>{car.price}</small>
                  </span>
                  <span className="vehicle-tile__arrow" aria-hidden="true">
                    <ArrowRight size={18} weight="light" />
                  </span>
                </span>
              </span>
            </span>
            <span className="vehicle-tile__index">{String(index + 1).padStart(2, '0')}</span>
          </Link>
        ))}
      </div>
      <div className="rail-controls" aria-label="Điều khiển danh sách xe">
        <button type="button" onClick={() => move(-1)} aria-label="Xem xe phía trước">
          <ArrowLeft size={20} weight="light" />
        </button>
        <button type="button" onClick={() => move(1)} aria-label="Xem xe tiếp theo">
          <ArrowRight size={20} weight="light" />
        </button>
      </div>
    </>
  )
}

export function HomePage() {
  const root = useRef(null)
  const location = useLocation()
  const [activeGroup, setActiveGroup] = useState('personal')
  const [storyIndex, setStoryIndex] = useState(0)
  const { cars } = useVehicleCatalog()
  const { data: homeContent } = usePageContent('home')
  const stories = homeContent?.testimonials || []
  const heroCar = cars.find((car) => car.id === homeContent?.hero?.vehicleId)
    || cars.find((car) => car.featured && car.category === 'personal')
    || cars[0]
  const flagshipVehicles = ['vf8', 'vf9']
    .map((id) => cars.find((car) => car.id === id))
    .filter(Boolean)

  const vehicles = useMemo(
    () => cars.filter((car) => car.category === activeGroup),
    [cars, activeGroup],
  )

  useEffect(() => {
    if (location.hash === '#models-service') setActiveGroup('fleet')
    if (location.hash === '#models-electric') setActiveGroup('personal')
  }, [location.hash])

  useGSAP(
    () => {
      // The testing UI has its catalogue synchronously available. In this branch,
      // wait for the API catalogue so GSAP measures the same complete DOM tree.
      if (cars.length === 0) return undefined

      // BACKEND/MEDIA CONTRACT: GSAP owns timing and movement; the API only selects
      // a whitelisted animationPreset and supplies correctly prepared media. Do not
      // send executable animation code or arbitrary selectors from CMS/backend.
      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      if (reduced) {
        gsap.set('[data-hero-reveal]', { opacity: 1, y: 0 })
        gsap.set('.home-hero__car', { opacity: 1 })
        return
      }

      const heroTimeline = gsap.timeline({ defaults: { ease: 'power4.out' } })
      heroTimeline
        .fromTo('.home-hero__car', { opacity: 0 }, { opacity: 1, duration: 1.25 })
        .fromTo(
          '[data-hero-reveal]',
          { y: 58, opacity: 0, filter: 'blur(10px)' },
          { y: 0, opacity: 1, filter: 'blur(0px)', duration: 0.95, stagger: 0.1 },
          '-=0.9',
        )

      gsap.fromTo(
        '.scroll-drive__car',
        { xPercent: -125, rotate: -0.6 },
        {
          xPercent: 118,
          rotate: 0.6,
          ease: 'none',
          scrollTrigger: {
            trigger: '.scroll-drive',
            start: 'top bottom',
            end: 'bottom top',
            scrub: 1,
          },
        },
      )

      gsap.fromTo(
        '.scroll-drive__copy',
        { y: 70, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: '.scroll-drive',
            start: 'top 72%',
            end: 'center 55%',
            scrub: 0.8,
          },
        },
      )

      gsap.fromTo(
        '.factory-film__media',
        { scale: 0.86, opacity: 0.3 },
        {
          scale: 1,
          opacity: 1,
          ease: 'none',
          scrollTrigger: {
            trigger: '.factory-film',
            start: 'top 88%',
            end: 'center 55%',
            scrub: 1,
          },
        },
      )

      gsap.fromTo(
        '.road-chapter__media img',
        { scale: 1.13 },
        {
          scale: 1,
          ease: 'none',
          scrollTrigger: {
            trigger: '.road-chapter',
            start: 'top bottom',
            end: 'bottom top',
            scrub: 1,
          },
        },
      )

      gsap.fromTo(
        '.factory-origin__media',
        { scale: 0.88, opacity: 0.28 },
        {
          scale: 1,
          opacity: 1,
          ease: 'none',
          scrollTrigger: { trigger: '.factory-origin', start: 'top 88%', end: 'center 58%', scrub: 1 },
        },
      )

      gsap.fromTo(
        '.flagship-passage__card:first-child',
        { xPercent: -18, opacity: 0 },
        {
          xPercent: 0,
          opacity: 1,
          ease: 'none',
          scrollTrigger: { trigger: '.flagship-passage', start: 'top 82%', end: 'center 54%', scrub: 0.9 },
        },
      )

      gsap.fromTo(
        '.flagship-passage__card:last-child',
        { xPercent: 18, opacity: 0 },
        {
          xPercent: 0,
          opacity: 1,
          ease: 'none',
          scrollTrigger: { trigger: '.flagship-passage', start: 'top 82%', end: 'center 54%', scrub: 0.9 },
        },
      )

      gsap.fromTo(
        '.home-action__model',
        { xPercent: -22, opacity: 0 },
        {
          xPercent: 0,
          opacity: 0.8,
          ease: 'none',
          scrollTrigger: { trigger: '.home-action', start: 'top 82%', end: 'center 50%', scrub: 0.9 },
        },
      )

      gsap.utils.toArray('.technology-panel').forEach((panel) => {
        gsap.fromTo(
          panel,
          { opacity: 0.24, scale: 0.88 },
          {
            opacity: 1,
            scale: 1,
            ease: 'none',
            scrollTrigger: {
              trigger: panel,
              start: 'top 88%',
              end: 'center 58%',
              scrub: 1,
            },
          },
        )
      })

      const refreshFrame = window.requestAnimationFrame(() => ScrollTrigger.refresh())

      return () => {
        window.cancelAnimationFrame(refreshFrame)
      }
    },
    { scope: root, dependencies: [cars.length], revertOnUpdate: true },
  )

  const nextStory = (direction) => {
    setStoryIndex((current) => (current + direction + stories.length) % stories.length)
  }

  return (
    <AppShell>
      <main ref={root} id="main-content" className="page page--home">
        <section className="home-hero" aria-labelledby="home-title">
          <div className="home-hero__ghost" aria-hidden="true">
            VINFAST
          </div>
          <div className="home-hero__copy">
            <p className="home-hero__kicker" data-hero-reveal>
              Ô tô điện VinFast
            </p>
            <h1 id="home-title" data-hero-reveal>
              Chọn chiếc xe.
              <br />
              Lái theo cách của bạn.
            </h1>
            <p className="home-hero__lead" data-hero-reveal>
              Xem từng mẫu xe qua hình ảnh thật, đối chiếu thông số chính thức và giữ lịch lái thử chỉ trong vài phút.
            </p>
            <div className="home-hero__actions" data-hero-reveal>
              <IslandButton to="/#models" variant="dark">
                Khám phá ô tô
              </IslandButton>
              <IslandButton to="/booking" variant="light">
                Đặt lịch lái thử
              </IslandButton>
            </div>
          </div>
          <div className="home-hero__visual" aria-hidden="true">
            <SmartImage
              className="home-hero__car"
              src={heroCar?.studioShot?.src}
              alt=""
              fit="contain"
              eager
            />
            <span className="home-hero__line" />
          </div>
          <a className="home-hero__scroll" href="#models">
            <span>Cuộn để khám phá</span>
            <span className="home-hero__scroll-line" />
          </a>
        </section>

        <section className="road-chapter" aria-labelledby="road-chapter-title">
          <div className="road-chapter__media">
            <SmartImage src={roadBanner} alt="Hai mẫu ô tô điện VinFast trên cung đường núi" />
          </div>
          <div className="road-chapter__veil" aria-hidden="true" />
          <div className="section-frame road-chapter__copy">
            <p className="eyebrow">Một dải sản phẩm · nhiều nhịp sống</p>
            <h2 id="road-chapter-title">Đi xa hơn, theo cách yên tĩnh hơn.</h2>
            <Link to="/charging">Khám phá năng lượng cho hành trình <ArrowRight size={18} weight="light" /></Link>
          </div>
        </section>

        {/* TODO [BACKEND/HOME MEDIA]: `factoryFilm` and `factoryAerial` are two
            independent CMS blocks. Do not composite the aerial image into this
            video slot; preserve their separate ordering and focal points. */}
        <section id="factory-film" className="factory-film" aria-labelledby="factory-film-title">
          <div className="factory-film__media">
            <video src={factoryFilm} autoPlay muted loop playsInline preload="auto" aria-label="Dây chuyền lắp ráp VinFast" />
            <div className="factory-film__veil" aria-hidden="true" />
            <div className="factory-film__copy">
              <p>Từ dây chuyền lắp ráp</p>
              <h2 id="factory-film-title">Mỗi hành trình bắt đầu từ một chuyển động được chế tạo chính xác.</h2>
              <span>Nhà máy VinFast · Hải Phòng</span>
            </div>
          </div>
        </section>

        <section id="factory-origin" className="factory-origin" aria-labelledby="factory-origin-title">
          <div className="section-frame factory-origin__grid">
            <Reveal className="factory-origin__copy">
              <p className="eyebrow">Từ Hải Phòng</p>
              <h2 id="factory-origin-title">Một tổ hợp dành cho những chuyển động quy mô lớn.</h2>
              <p>
                Sau nhịp lắp ráp cận cảnh là toàn bộ không gian nơi mỗi chiếc xe đi qua nhiều công đoạn trước khi bắt đầu hành trình trên đường.
              </p>
            </Reveal>
            <figure className="factory-origin__media">
              <SmartImage src={factoryAerial} alt="Toàn cảnh tổ hợp sản xuất VinFast tại Hải Phòng" />
              <figcaption><span>01</span>Tổ hợp sản xuất VinFast · Hải Phòng</figcaption>
            </figure>
          </div>
        </section>

        <section className="model-marquee" aria-label="Danh sách dòng xe">
          <div className="model-marquee__track">
            {[...cars, ...cars].map((car, index) => (
              <span key={`${car.id}-${index}`}>{car.navName}</span>
            ))}
          </div>
        </section>

        <section className="models-section" id="models">
          <div className="section-frame">
            <Reveal className="section-heading section-heading--wide">
              <p className="eyebrow">Ô tô</p>
              <h2>
                Hai dòng xe, một lựa chọn vừa với{' '}
                <span
                  className="inline-image inline-image--road"
                  style={{ '--inline-image-url': `url(${carImage('VF8/banner.webp')})` }}
                  aria-hidden="true"
                />{' '}
                hành trình của bạn.
              </h2>
            </Reveal>

            <div className="model-tabs" role="tablist" aria-label="Nhóm sản phẩm">
              {carGroups.map((group) => (
                <button
                  key={group.id}
                  id={group.id === 'personal' ? 'models-electric' : 'models-service'}
                  type="button"
                  role="tab"
                  aria-selected={activeGroup === group.id}
                  onClick={() => setActiveGroup(group.id)}
                >
                  <span>{group.label}</span>
                  <small>{group.description}</small>
                </button>
              ))}
            </div>

            <VehicleRail vehicles={vehicles} />
          </div>
        </section>

        <section id="flagship" className="flagship-passage" aria-labelledby="flagship-title">
          <div className="section-frame">
            <Reveal className="flagship-passage__heading">
              <p className="eyebrow">Hai dấu ấn đường dài</p>
              <h2 id="flagship-title">Không gian cho từng cách bạn đi.</h2>
            </Reveal>
            <div className="flagship-passage__grid">
              {flagshipVehicles.map((car) => (
                <Link className="flagship-passage__card" to={`/models/${car.id}`} key={car.id}>
                  <span className="flagship-passage__index" aria-hidden="true">
                    {car.id === 'vf8' ? '08' : '09'}
                  </span>
                  <SmartImage
                    className={`flagship-passage__media vehicle-shot vehicle-shot--${car.studioShot.mode}`}
                    src={car.studioShot.src}
                    alt={`${car.name} — ảnh xe studio đã tách nền`}
                  />
                  <span className="flagship-passage__copy">
                    <small>{car.body} · {car.seats}</small>
                    <strong>{car.name}</strong>
                    <ArrowRight size={20} weight="light" />
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </section>

        <section className="vivi-intro" id="vivi">
          <div className="section-frame vivi-intro__grid">
            <Reveal className="vivi-intro__portrait">
              <div className="double-bezel">
                <div className="double-bezel__core">
                  <img src={viviPortrait} alt="ViVi, trợ lý đặt lịch lái thử VinFast" />
                </div>
              </div>
            </Reveal>
            <Reveal className="vivi-intro__copy" delay={0.08}>
              <p className="eyebrow">ViVi đặt lịch</p>
              <h2>Bạn nói nhu cầu. ViVi nối đúng xe, đúng nơi và đúng giờ.</h2>
              <p>
                ViVi không thay bạn chọn xe. Trợ lý ghi nhớ mẫu vừa xem, tìm showroom đang có xe lái thử và chỉ đưa ra những khung giờ thực sự phù hợp.
              </p>
              <div className="vivi-intro__steps">
                <span>Chọn mẫu xe</span><span>Chọn showroom có xe</span><span>Giữ khung giờ</span>
              </div>
              <IslandButton to="/booking" variant="dark">
                Bắt đầu cùng ViVi
              </IslandButton>
            </Reveal>
          </div>
        </section>

        <section className="scroll-drive" aria-label="Chuyển động xe theo thao tác cuộn">
          <div className="scroll-drive__copy">
            <p className="eyebrow">Chuyển động thuần điện</p>
            <h2>Chạm để xem. Cuộn để chiếc xe bắt đầu hành trình.</h2>
          </div>
          <div className="scroll-drive__road" aria-hidden="true"><span /><span /><span /></div>
          <SmartImage
            className="scroll-drive__car"
            src={cars.find((car) => car.id === 'vf8-the-he-moi')?.intro}
            alt="VF 8 Thế hệ mới đang di chuyển"
          />
        </section>

        <section className="ownership-section" id="ecosystem">
          <div className="section-frame">
            <Reveal className="section-heading section-heading--split">
              <div>
                <p className="eyebrow">Sống cùng xe điện</p>
                <h2>Mọi thứ cần thiết, đã nằm trong một hệ sinh thái.</h2>
              </div>
              <p>
                Từ sạc, bảo hành đến việc tìm showroom gần nhất, trải nghiệm được nối thành một hành trình liền mạch và dễ hiểu.
              </p>
            </Reveal>

            <div className="ownership-bento">
              <Reveal className="bento-block bento-block--main">
                <Link to="/charging" className="double-bezel double-bezel--dark">
                  <div className="double-bezel__core bento-charge">
                    <SmartImage
                      src={carImage('VF9/cs-home-charger.webp')}
                      alt="Bộ sạc tại nhà VinFast"
                    />
                    <div className="bento-charge__copy">
                      <BatteryCharging size={28} weight="light" />
                      <h3>Sạc tại nơi bạn dừng.</h3>
                      <p>Chủ động nạp năng lượng tại nhà hoặc tiếp tục hành trình qua mạng lưới trạm sạc.</p>
                    </div>
                  </div>
                </Link>
              </Reveal>

              <Reveal className="bento-block bento-block--support" delay={0.08}>
                <Link to="/after-sales" className="double-bezel">
                  <div className="double-bezel__core bento-support">
                    <ShieldCheck size={28} weight="light" />
                    <div>
                      <h3>Bảo hành dài hạn</h3>
                      <p>Thông tin chính sách hiển thị rõ theo từng mẫu xe và phiên bản.</p>
                    </div>
                  </div>
                </Link>
              </Reveal>

              <Reveal className="bento-block bento-block--network" delay={0.14}>
                <div className="double-bezel">
                  <div className="double-bezel__core bento-network">
                    <MapPin size={28} weight="light" />
                    <div>
                      <h3>Showroom gần bạn</h3>
                      <p>Chọn đúng mẫu, đúng khu vực và khung giờ trước khi di chuyển.</p>
                    </div>
                    <span className="network-pulse" aria-hidden="true" />
                  </div>
                </div>
              </Reveal>
            </div>
          </div>
        </section>

        <section className="technology-story" id="technology">
          <div className="section-frame technology-story__grid">
            <div className="technology-story__intro">
              <p className="eyebrow">Cảm nhận trước khi quyết định</p>
              <h2>Không chỉ nhìn xe. Hãy đọc cách chiếc xe sống cùng bạn.</h2>
              <p>
                Mỗi trang xe là một câu chuyện hình ảnh: ngoại thất, khoang lái, vận hành và dữ liệu kỹ thuật được dẫn theo nhịp cuộn.
              </p>
              <IslandButton to="/models/vf8" variant="dark">
                Xem trải nghiệm VF 8
              </IslandButton>
            </div>

            <div className="technology-story__panels">
              {/* Ảnh được chỉ định thẳng theo nội dung của tiêu đề: khoang lái đi với ảnh
                  vô lăng/màn hình, hình khối đi với ảnh ngoại thất, không gian đi với ảnh cabin. */}
              {[
                {
                  id: 'cockpit',
                  car: 'vf8',
                  image: carImage('VF8/ai.webp'),
                  title: 'Khoang lái tập trung',
                  copy: 'Vô lăng, màn hình trung tâm và các phím thao tác nằm gọn trong tầm với của người lái.',
                },
                {
                  id: 'form',
                  car: 'vf7',
                  image: carImage('VF7/vf7-passion.webp'),
                  title: 'Hình khối có chủ đích',
                  copy: 'Đường nét khí động học tạo cá tính mà vẫn phục vụ hiệu quả vận hành.',
                },
                {
                  id: 'cabin',
                  car: 'vf9',
                  image: carImage('VF9/int-slide-4.webp'),
                  title: 'Không gian cho chuyến dài',
                  copy: 'Hàng ghế sau với tựa đầu, màn hình giải trí và tiện nghi dành cho hành khách.',
                },
              ].map((item) => {
                const car = cars.find((entry) => entry.id === item.car)
                if (!car) return null

                return (
                  <article className="technology-panel" key={item.id}>
                    <div className="double-bezel double-bezel--dark">
                      <div className="double-bezel__core">
                        <SmartImage src={item.image} alt={`${car.name} — ${item.title}`} />
                      </div>
                    </div>
                    <div className="technology-panel__caption">
                      <h3>{item.title}</h3>
                      <p>{item.copy}</p>
                    </div>
                  </article>
                )
              })}
            </div>
          </div>
        </section>

        {stories.length > 0 && <section className="voices-section">
          <div className="section-frame voices-section__grid">
            <Reveal className="voices-section__title">
              <p className="eyebrow">Sau một vòng lái</p>
              <h2>Quyết định trở nên rõ ràng hơn.</h2>
            </Reveal>

            <div className="voice-carousel" aria-live="polite">
              <span className="voice-carousel__quote" aria-hidden="true">“</span>
              <blockquote key={storyIndex}>
                <p>{stories[storyIndex].quote}</p>
                <footer>
                  <strong>{stories[storyIndex].name}</strong>
                  <span>{stories[storyIndex].role}</span>
                </footer>
              </blockquote>
              <div className="voice-carousel__controls">
                <span>{String(storyIndex + 1).padStart(2, '0')} / {String(stories.length).padStart(2, '0')}</span>
                <div>
                  <button type="button" onClick={() => nextStory(-1)} aria-label="Câu chuyện trước">
                    <ArrowLeft size={20} weight="light" />
                  </button>
                  <button type="button" onClick={() => nextStory(1)} aria-label="Câu chuyện tiếp theo">
                    <ArrowRight size={20} weight="light" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>}

        {/* TODO [BACKEND/HOME CTA]: This CTA accepts exactly one vehicle render.
            Background is presentation CSS; never return a second car as backdrop. */}
        <section id="home-action" className="home-action">
          <div className="home-action__backdrop" aria-hidden="true" />
          <SmartImage className="home-action__model" src={vf9Sculpture} alt="" aria-hidden="true" />
          <div className="section-frame home-action__content">
            <Reveal>
              <p className="eyebrow">Bắt đầu từ cảm giác sau tay lái</p>
              <h2>Chọn xe. Chọn nơi. Chọn giờ.</h2>
              <p>ViVi sẽ giữ lại toàn bộ lựa chọn để bạn hoàn tất lịch thử xe trong một luồng duy nhất.</p>
              <div className="home-action__buttons">
                <IslandButton to="/booking" variant="light">
                  Đặt lịch ngay
                </IslandButton>
                <IslandButton to="/agent" variant="ghost-light">
                  Hỏi ViVi trước
                </IslandButton>
              </div>
            </Reveal>
          </div>
        </section>

        <footer className="site-footer">
          <div className="section-frame site-footer__inner">
            <div>
              <strong>VINFAST</strong>
              <p>Thiết kế trải nghiệm xem xe và đặt lịch lái thử.</p>
            </div>
            <nav aria-label="Liên kết cuối trang">
              <a href="#models">Ô tô</a>
              <a href="#technology">Công nghệ</a>
              <Link to="/after-sales">Hậu mãi</Link>
              <Link to="/charging">Pin & trạm sạc</Link>
              <Link to="/booking">Đặt lịch</Link>
              <Link to="/agent">Trợ lý ViVi</Link>
            </nav>
            <p className="site-footer__legal">
              Thông số được tổng hợp từ brochure chính thức và có thể thay đổi theo phiên bản, điều kiện vận hành hoặc chính sách của nhà sản xuất.
            </p>
          </div>
        </footer>
      </main>
    </AppShell>
  )
}
