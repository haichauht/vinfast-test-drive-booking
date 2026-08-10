/**
 * pages/CarDetailPage.jsx — TRANG CHI TIẾT XE tại đường dẫn /models/:carId (vd: /models/vf9).
 *
 * Dữ liệu: useVehicleDetail(carId) cho mẫu xe đang xem, useVehicleCatalog() để tìm "xe tiếp theo".
 * ID không có trong catalogue → hiện màn "Không tìm thấy mẫu xe" thay vì trang lỗi.
 *
 * Thứ tự các mục trên trang:
 *  1. Hero — tên xe cỡ lớn, ảnh xe chạy vào từ trái          (.detail-hero)
 *  2. Video nội thất (CHỈ mẫu limo-green)                     (.detail-film)
 *  3. Popup gợi ý đặt lịch, tự hiện sau 2,2 giây              (.test-drive-nudge)
 *  4. Câu tuyên ngôn — chữ sáng dần từng từ khi cuộn          (.car-manifesto)
 *  5. Model GLB tương tác VF3/VF9 + cinematic chạy ngang      (Vehicle3DExperience)
 *  6. Thước phim giới thiệu, nếu backend có video             (ModelFilm, ~dòng 68)
 *  7. Thông số nổi bật                                        (.detail-specs, id="specifications")
 *  8. Các chương ảnh: ngoại thất → khoang lái → chi tiết      (.detail-story)
 *  9. Lưới ảnh đầy đủ, chỉ hiện khi có hơn 3 ảnh              (.detail-media)
 * 10. Bảng màu bấm đổi được, cần ít nhất 2 màu                (ColorExplorer, ~dòng 16)
 * 11. Nguồn dữ liệu + link brochure PDF                       (.brochure-note)
 * 12. CTA cuối + link sang xe tiếp theo                       (.detail-action)
 * 13. Thanh nổi dưới đáy: tên xe, giá, nút đặt lịch           (.detail-booking-dock)
 *
 * ANIMATION (khối useGSAP ~dòng 127) — phần tinh vi nhất dự án:
 * - Xe chạy vào màn hình. Lần đầu xem mẫu này chạy dài (-132%, 1,7 giây), các lần sau
 *   ngắn hơn (-34%, 0,95 giây) — trạng thái ghi trong sessionStorage theo từng mẫu xe.
 * - Chỉ chạy kiểu đó khi backend có `motionImage` (ảnh tách nền). Không có thì xe phóng to dần.
 * - Chữ tuyên ngôn sáng dần từng từ, ảnh từng chương phóng to theo thao tác cuộn.
 * - VF3/VF9: GLB chạy xuyên trái → phải trong 1,9 giây khi sân khấu đã hiện rõ,
 *   sau đó popup thành model xoay/zoom.
 *
 * sessionStorage lưu 3 khoá (chỉ ID và cờ giao diện, KHÔNG lưu thông tin cá nhân):
 * last-viewed-car · test-drive-nudge:<id> · vinfast-intro-seen:<id>.
 * Muốn xem lại animation lần đầu hoặc popup gợi ý: mở tab ẩn danh, hoặc xoá sessionStorage.
 */
import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useGSAP } from '@gsap/react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { ArrowLeft, ArrowRight, Check, FileText, X } from '@phosphor-icons/react'
import { AppShell } from '../components/AppShell'
import { IslandButton } from '../components/IslandButton'
import { Reveal } from '../components/Reveal'
import { SmartImage } from '../components/SmartImage'
import { SiteFooter } from '../components/SiteFooter'
import { Vehicle3DExperience } from '../components/Vehicle3DExperience'
import { useVehicleCatalog, useVehicleDetail } from '../hooks/useSiteData'
import { limoInteriorFilm } from '../data/media'

gsap.registerPlugin(useGSAP, ScrollTrigger)

function ColorExplorer({ car }) {
  const availableColors = car.colors.filter((color) => color.image)
  const [selectedIndex, setSelectedIndex] = useState(0)
  const selected = availableColors[selectedIndex]
  const displayImage = selected?.image

  if (availableColors.length < 2) return null

  return (
    <section className="color-explorer" aria-labelledby="color-title">
      <div className="section-frame color-explorer__grid">
        <div className="color-explorer__copy">
          <p className="eyebrow">Bảng màu</p>
          <h2 id="color-title">Một sắc độ cho cá tính riêng.</h2>
          <p>
            Chọn một màu để xem chiếc xe đổi diện mạo. Sắc độ ngoài đời có thể khác đôi chút tuỳ ánh sáng và góc nhìn.
          </p>
          <div className="color-list" role="radiogroup" aria-label={`Chọn màu ${car.name}`}>
            {availableColors.map((color, index) => (
              <button
                key={`${color.name}-${index}`}
                className={selectedIndex === index ? 'is-active' : ''}
                type="button"
                role="radio"
                aria-checked={selectedIndex === index}
                onClick={() => setSelectedIndex(index)}
              >
                <span className="color-list__swatch" style={{ background: color.hex }} aria-hidden="true" />
                <span>{color.name}</span>
                {selectedIndex === index && <Check size={15} weight="light" aria-hidden="true" />}
              </button>
            ))}
          </div>
        </div>
        <div className="double-bezel color-explorer__visual">
          <div className="double-bezel__core">
            <SmartImage
              key={displayImage}
              src={displayImage}
              alt={`${car.name} màu ${selected?.name || 'đang chọn'}`}
            />
            <div className="color-explorer__caption">
              <span>{car.name}</span>
              <strong>{selected?.name}</strong>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function ModelFilm({ car }) {
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const film = car.presentationFilm

  if (!film) return null

  return (
    <section id="model-film" className="model-film" aria-labelledby={`model-film-${car.id}`}>
      <div className="model-film__stage">
        <video
          className="model-film__video"
          src={film.src}
          poster={film.poster || car.hero}
          autoPlay={!reducedMotion}
          muted
          loop
          playsInline
          preload="metadata"
          aria-label={`Thước phim giới thiệu ${car.name}`}
        />
        <div className="model-film__veil" aria-hidden="true" />
        <div className="model-film__copy" data-film-layer>
          <p>{film.eyebrow}</p>
          <h2 id={`model-film-${car.id}`}>{film.title}</h2>
          <span>{film.copy}</span>
        </div>
      </div>
    </section>
  )
}

export function CarDetailPage() {
  const { carId } = useParams()
  const { car } = useVehicleDetail(carId)
  const { cars } = useVehicleCatalog()
  const root = useRef(null)
  const [showTestDriveNudge, setShowTestDriveNudge] = useState(false)
  const [exploring3d, setExploring3d] = useState(false)

  useEffect(() => {
    if (!car) return undefined
    setExploring3d(false)
    setShowTestDriveNudge(false)
    const dismissed = window.sessionStorage.getItem(`vinfast:test-drive-nudge:${car.id}`)
    if (dismissed) return undefined

    const timer = window.setTimeout(() => setShowTestDriveNudge(true), 2200)
    return () => window.clearTimeout(timer)
  }, [car])

  const dismissNudge = () => {
    // TODO [BACKEND/ANALYTICS]: Emit test_drive_nudge_dismissed with vehicleId and
    // placement only. Do not send a name, phone, email or free-text value.
    if (car) window.sessionStorage.setItem(`vinfast:test-drive-nudge:${car.id}`, 'dismissed')
    setShowTestDriveNudge(false)
  }

  useGSAP(
    () => {
      if (!car) return

      // BACKEND/MEDIA CONTRACT: `motionImage` must follow the cutout requirements
      // documented in BACKEND_HANDOFF.md. The backend may choose a named preset,
      // while duration/easing/selectors stay controlled by this frontend.
      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      const visitKey = `vinfast-intro-seen:${car.id}`
      const firstVisit = !window.sessionStorage.getItem(visitKey)
      window.sessionStorage.setItem(visitKey, 'true')

      if (reduced) {
        gsap.set('.detail-hero__car, [data-detail-copy], .model-film__stage, [data-film-layer]', {
          opacity: 1,
          xPercent: 0,
          x: 0,
          y: 0,
          scale: 1,
        })
      } else {
        const intro = gsap.timeline({ defaults: { ease: 'power4.out' } })
        const carFrom = car.motionImage
          ? { xPercent: firstVisit ? -132 : -34, opacity: 0, rotate: firstVisit ? -1.2 : 0 }
          : { xPercent: 0, scale: 0.92, opacity: 0 }
        intro
          .fromTo('.detail-hero__car', carFrom, { xPercent: 0, x: 0, scale: 1, opacity: 1, rotate: 0, duration: firstVisit ? 1.7 : 0.95 })
          .fromTo(
            '[data-detail-copy]',
            { y: 48, opacity: 0, filter: 'blur(8px)' },
            { y: 0, opacity: 1, filter: 'blur(0px)', duration: 0.9, stagger: 0.1 },
            '-=0.72',
          )
      }

      gsap.to('.detail-hero__car', {
        x: car.motionImage ? 72 : 0,
        ease: 'none',
        scrollTrigger: {
          trigger: '.detail-hero',
          start: 'top top',
          end: 'bottom top',
          scrub: 1,
        },
      })

      gsap.fromTo(
        '.manifesto-word',
        { opacity: 0.12 },
        {
          opacity: 1,
          stagger: 0.08,
          ease: 'none',
          scrollTrigger: {
            trigger: '.car-manifesto',
            start: 'top 72%',
            end: 'bottom 48%',
            scrub: 1,
          },
        },
      )

      if (car.presentationFilm) {
        const filmTimeline = gsap.timeline({
          scrollTrigger: {
            trigger: '.model-film',
            start: 'top 82%',
            end: 'center 48%',
            scrub: 1,
          },
        })
        filmTimeline
          .fromTo('.model-film__stage', { y: 56, scale: 0.94, opacity: 0.42 }, { y: 0, scale: 1, opacity: 1, ease: 'none' })
          .fromTo('.model-film__video', { scale: 1.07 }, { scale: 1, ease: 'none' }, '<')
          .fromTo('[data-film-layer]', { y: 30, opacity: 0 }, { y: 0, opacity: 1, stagger: 0.06, ease: 'power3.out' }, 0.18)
      }

      gsap.utils.toArray('.detail-chapter__media').forEach((mediaEl) => {
        gsap.fromTo(
          mediaEl,
          { scale: 0.82, opacity: 0.2 },
          {
            scale: 1,
            opacity: 1,
            ease: 'none',
            scrollTrigger: {
              trigger: mediaEl,
              start: 'top 90%',
              end: 'center 62%',
              scrub: 1,
            },
          },
        )
      })

      gsap.utils.toArray('.detail-media-grid__item').forEach((mediaEl) => {
        gsap.fromTo(mediaEl, { scale: 0.9, opacity: 0.35 }, {
          scale: 1,
          opacity: 1,
          ease: 'none',
          scrollTrigger: { trigger: mediaEl, start: 'top 92%', end: 'center 62%', scrub: 0.8 },
        })
      })

    },
    { scope: root, dependencies: [carId, car] },
  )

  if (!car) {
    return (
      <AppShell>
        <main id="main-content" className="not-found">
          <div className="not-found__inner">
            <p className="eyebrow">Không tìm thấy mẫu xe</p>
            <h1>Đường dẫn này chưa có trong catalogue.</h1>
            <p>Hãy quay lại dải sản phẩm để chọn một mẫu xe đang có dữ liệu.</p>
            <IslandButton to="/#models" variant="dark">
              Xem tất cả ô tô
            </IslandButton>
          </div>
        </main>
      </AppShell>
    )
  }

  // TODO [BACKEND/CATALOGUE]: The API must return deterministic sortOrder (or an
  // explicit nextVehicleId) so "Xem mẫu tiếp theo" does not change between requests.
  const nextCar = cars.length
    ? cars[(cars.findIndex((item) => item.id === car.id) + 1) % cars.length]
    : null
  const manifesto = `${car.tagline} ${car.description}`.split(' ')
  const carMedia = (car.media || car.gallery || [])
    .map((asset, index) => {
      const fallbackLabel = `Góc nhìn ${String(index + 1).padStart(2, '0')}`
      if (typeof asset === 'string') return { src: asset, alt: '', label: fallbackLabel }
      return {
        src: asset.src || '',
        alt: asset.alt || asset.label || '',
        label: asset.label || fallbackLabel,
      }
    })
    .filter((asset) => asset.src)

  return (
    <AppShell>
      <main ref={root} id="main-content" className="page page--detail">
        <section className="detail-hero" aria-labelledby="detail-title">
          <div className="detail-hero__wash" aria-hidden="true" />
          <div className="detail-hero__model-word" aria-hidden="true">{car.name}</div>
          <div className="detail-hero__road" aria-hidden="true"><span /></div>
          <Link className="detail-back" to="/#models" data-detail-copy>
            <ArrowLeft size={17} weight="light" />
            Tất cả ô tô
          </Link>
          <div className="detail-hero__copy">
            <p data-detail-copy>{car.body}</p>
            <h1 id="detail-title" data-detail-copy>{car.name}</h1>
            <span data-detail-copy>{car.tagline}</span>
          </div>
          <SmartImage
            className={`detail-hero__car ${car.motionImage ? 'is-motion-cutout' : 'is-static-asset'}`}
            src={car.motionImage || car.intro}
            alt={`${car.name} toàn cảnh`}
            eager
          />
          <div className="detail-hero__actions" data-detail-copy>
            <IslandButton to={`/booking?car=${car.id}`} variant="light">
              Đặt lịch lái thử
            </IslandButton>
            <a href="#specifications">Xem thông số</a>
          </div>
        </section>

        {car.id === 'limo-green' && (
          <section className="detail-film" aria-labelledby="detail-film-title">
            <video src={limoInteriorFilm} autoPlay muted loop playsInline preload="metadata" />
            <div className="detail-film__veil" aria-hidden="true" />
            <div className="section-frame detail-film__copy">
              <p className="eyebrow">Không gian Limo Green</p>
              <h2 id="detail-film-title">Ba hàng ghế được nhìn trong chuyển động thật.</h2>
            </div>
          </section>
        )}

        {showTestDriveNudge && !exploring3d && (
          <aside className="test-drive-nudge" aria-live="polite">
            <button type="button" onClick={dismissNudge} aria-label="Đóng gợi ý đặt lịch">
              <X size={16} weight="light" />
            </button>
            <span>ViVi đã ghi nhớ mẫu xe bạn đang xem</span>
            <strong>Bạn muốn lái thử {car.name}?</strong>
            <p>Tiếp tục với đúng mẫu xe này trong không gian đặt lịch cùng ViVi.</p>
            <Link to={`/booking?car=${car.id}`}>Đặt lịch lái thử</Link>
          </aside>
        )}

        <section className="car-manifesto">
          <div className="section-frame">
            <p aria-label={`${car.tagline} ${car.description}`}>
              {manifesto.map((word, index) => (
                <span className="manifesto-word" key={`${word}-${index}`} aria-hidden="true">
                  {word}{' '}
                </span>
              ))}
            </p>
          </div>
        </section>

        <Vehicle3DExperience car={car} onEnter={() => {
          setExploring3d(true)
          setShowTestDriveNudge(false)
        }} />

        <ModelFilm car={car} />

        <section className="detail-specs" id="specifications">
          <div className="section-frame">
            <Reveal className="detail-specs__heading">
              <p className="eyebrow">Thông số nổi bật</p>
              <h2>Dữ liệu quan trọng, không làm bạn phân tâm.</h2>
              <p>{typeof car.brochure === 'object' ? car.brochure?.title : car.brochure}</p>
            </Reveal>
            <div className="spec-strip">
              {car.specs.map((spec, index) => (
                <Reveal className="spec-strip__item" delay={index * 0.06} key={spec.label}>
                  <strong>{spec.value}</strong>
                  <span>{spec.label}</span>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        <section className="detail-story">
          <div className="section-frame detail-story__grid">
            <aside className="detail-story__aside">
              <p className="eyebrow">Nhìn gần hơn</p>
              <h2>Thiết kế được kể bằng từng góc nhìn.</h2>
              <p>
                Các góc nhìn được sắp theo đúng thứ tự bạn thường quan sát một chiếc xe: dáng ngoài trước, rồi tới chỗ ngồi và những chi tiết bên trong.
              </p>
            </aside>

            <div className="detail-story__chapters">
              {/* Tiêu đề và ảnh đi theo cặp từ backend media payload, không gán theo
                  thứ tự, nên ảnh nội thất không còn bị chú thích là "hình khối". */}
              {car.chapters.map((chapter) => (
                <article className="detail-chapter" key={chapter.src}>
                  <div className={`double-bezel detail-chapter__media ${chapter.tone === 'dark' ? 'double-bezel--dark' : ''}`}>
                    <div className={`double-bezel__core detail-chapter__frame is-${chapter.tone}`}>
                      <SmartImage src={chapter.src} alt={`${car.name} — ${chapter.title.toLowerCase()}`} />
                    </div>
                  </div>
                  <div className="detail-chapter__copy">
                    <h3>{chapter.title}</h3>
                    <p>{chapter.copy}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        {carMedia.length > 3 && (
          <section className="detail-media" aria-labelledby="detail-media-title">
            <div className="section-frame">
              <Reveal className="detail-media__heading">
                <p className="eyebrow">Toàn bộ góc nhìn</p>
                <h2 id="detail-media-title">Ngoại thất, khoang lái và công nghệ của {car.name}.</h2>
                <p>{carMedia.length} góc nhìn của {car.name}, từ ngoại thất đến khoang lái và chi tiết vận hành.</p>
              </Reveal>
              <div className="detail-media-grid">
                {carMedia.slice(3).map((asset, index) => (
                  <figure className="detail-media-grid__item" key={`${asset.src}-${index}`}>
                    <SmartImage src={asset.src} alt={asset.alt || `${car.name} · ${asset.label}`} />
                    <figcaption>{asset.label}</figcaption>
                  </figure>
                ))}
              </div>
            </div>
          </section>
        )}

        <ColorExplorer key={car.id} car={car} />

        <section className="brochure-note">
          <div className="section-frame brochure-note__inner">
            <FileText size={28} weight="light" />
            <div>
              <p className="eyebrow">Nguồn dữ liệu sản phẩm</p>
              {typeof car.brochure === 'object' ? (
                <h2>
                  <a href={car.brochure.url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'underline', color: 'inherit' }}>
                    {car.brochure.title}
                  </a>
                </h2>
              ) : (
                <h2>{car.brochure}</h2>
              )}
              <p>
                Thông số được lấy từ brochure chính thức của mẫu xe. Quãng đường thực tế còn phụ thuộc phiên bản, nhiệt độ, địa hình và thói quen lái.
              </p>
            </div>
          </div>
        </section>

        <section className="detail-action">
          <SmartImage src={car.actionMedia?.src || car.hero} alt="" aria-hidden="true" focalPoint={car.actionMedia?.focalPoint} />
          <div className="detail-action__wash" aria-hidden="true" />
          <div className="section-frame detail-action__content">
            <Reveal>
              <p className="eyebrow">Tiếp theo</p>
              <h2>Cảm nhận {car.name} trên đường thật.</h2>
              <p>Chọn showroom và khung giờ phù hợp, ViVi sẽ giúp bạn giữ lại lựa chọn.</p>
              <div className="detail-action__buttons">
                <IslandButton to={`/booking?car=${car.id}`} variant="light">
                  Đặt lịch lái thử
                </IslandButton>
                {nextCar && (
                  <IslandButton to={`/models/${nextCar.id}`} variant="ghost-light">
                    Xem {nextCar.name}
                  </IslandButton>
                )}
              </div>
            </Reveal>
          </div>
        </section>

        <SiteFooter />

        <div className="detail-booking-dock">
          <div>
            <strong>{car.name}</strong>
            <span>{car.price}</span>
          </div>
          <Link to={`/booking?car=${car.id}`}>
            Đặt lịch lái thử
            <span aria-hidden="true"><ArrowRight size={16} weight="light" /></span>
          </Link>
        </div>
      </main>
    </AppShell>
  )
}
