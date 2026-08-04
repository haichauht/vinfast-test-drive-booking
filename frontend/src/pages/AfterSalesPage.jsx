import { useRef } from 'react'
import { useGSAP } from '@gsap/react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import {
  ArrowDown,
  ArrowUpRight,
  BookOpen,
  CheckCircle,
  EnvelopeSimple,
  Headset,
  ShieldCheck,
} from '@phosphor-icons/react'
import { AppShell } from '../components/AppShell'
import { Reveal } from '../components/Reveal'
import { SmartImage } from '../components/SmartImage'
import { highVoltageWarranty, ownershipMedia } from '../data/ownership'

gsap.registerPlugin(useGSAP, ScrollTrigger)

const warrantyPrinciples = [
  {
    index: '01',
    title: 'Đúng nguyên nhân',
    copy: 'Áp dụng cho hư hỏng do lỗi phần mềm, chất lượng linh kiện hoặc lỗi lắp ráp của VinFast khi xe được sử dụng và bảo dưỡng đúng cách.',
  },
  {
    index: '02',
    title: 'Đúng phụ tùng',
    copy: 'Chi tiết thay thế trong bảo hành là phụ tùng chính hãng nhỏ nhất được VinFast cung cấp để khắc phục lỗi.',
  },
  {
    index: '03',
    title: 'Đúng hệ thống',
    copy: 'Chính sách có hiệu lực trên toàn Việt Nam và được thực hiện tại xưởng dịch vụ hoặc nhà phân phối VinFast ủy quyền.',
  },
]

const exclusions = [
  {
    title: 'Chậm đưa xe đi kiểm tra',
    copy: 'Hư hỏng kéo theo do trì hoãn đưa xe đến nhà phân phối hoặc xưởng dịch vụ sau khi phát hiện dấu hiệu bất thường không thuộc phạm vi bảo hành.',
  },
  {
    title: 'Báo lỗi sau khi hết hạn',
    copy: 'Hư hỏng xảy ra trong thời hạn nhưng được người sử dụng báo cáo sau khi chính sách đã hết hiệu lực có thể bị từ chối.',
  },
  {
    title: 'Chi phí phát sinh gián tiếp',
    copy: 'Trong phạm vi pháp luật cho phép, các khoản điện thoại, ăn ở, thuê phương tiện, đi lại, thiệt hại kinh doanh hoặc thời gian không nằm trong trách nhiệm bảo hành.',
  },
]

const questions = [
  {
    title: 'Chính sách mới có áp dụng cho xe đã mua trước đó?',
    copy: 'Chính sách mới áp dụng cho xe mua kể từ ngày chính sách có hiệu lực. Xe mua trước thời điểm đó tiếp tục theo chính sách hiệu lực tại ngày mua.',
  },
  {
    title: 'Pin chai có được bảo hành?',
    copy: 'Điều kiện suy giảm dung lượng và ngưỡng đánh giá được quy định trong Sổ bảo hành của từng xe. Hãy cung cấp số VIN cho xưởng dịch vụ để được kiểm tra theo đúng phiên bản.',
  },
  {
    title: 'Mua phụ tùng tại đại lý nhưng lắp bên ngoài có được bảo hành?',
    copy: 'Không. Phụ tùng mua nhưng không được thay thế tại xưởng dịch vụ hoặc nhà phân phối VinFast không thuộc chính sách bảo hành phụ tùng này.',
  },
  {
    title: 'Xe ngập nước có được bảo hành?',
    copy: 'Tình trạng ngập nước cần được xưởng dịch vụ kiểm tra nguyên nhân và phạm vi hư hỏng. Không tự khởi động hoặc can thiệp vào hệ thống điện áp cao.',
  },
]

export function AfterSalesPage() {
  const root = useRef(null)

  useGSAP(
    () => {
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

      gsap.fromTo(
        '.ownership-hero__media img',
        { scale: 1.12 },
        {
          scale: 1,
          ease: 'none',
          scrollTrigger: {
            trigger: '.ownership-hero',
            start: 'top top+=90',
            end: 'bottom top',
            scrub: 1,
          },
        },
      )

      gsap.fromTo(
        '.ownership-hero [data-intro]',
        { y: 54, opacity: 0 },
        { y: 0, opacity: 1, duration: 1, stagger: 0.09, ease: 'power4.out' },
      )

      gsap.utils.toArray('.policy-card').forEach((card, index) => {
        gsap.fromTo(
          card,
          { y: 42, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 0.85,
            delay: Math.min(index * 0.05, 0.15),
            ease: 'power3.out',
            scrollTrigger: { trigger: card, start: 'top 88%', once: true },
          },
        )
      })
    },
    { scope: root },
  )

  return (
    <AppShell>
      <main ref={root} id="main-content" className="page ownership-page ownership-page--care">
        <section className="ownership-hero ownership-hero--care" aria-labelledby="care-title">
          <div className="ownership-hero__media" aria-hidden="true">
            <SmartImage src={ownershipMedia.afterSalesHero} alt="" eager />
          </div>
          <div className="ownership-hero__veil" aria-hidden="true" />
          <div className="section-frame ownership-hero__content">
            <p className="ownership-hero__kicker" data-intro>Dịch vụ hậu mãi</p>
            <h1 id="care-title" data-intro>
              An tâm được<br />thiết kế dài lâu.
            </h1>
            <p data-intro>
              Phạm vi, thời hạn và cách nhận hỗ trợ được hệ thống lại từ chính sách bảo hành VinFast để bạn dễ tra cứu trước mỗi hành trình.
            </p>
            <a className="ownership-hero__scroll" href="#care-overview" data-intro>
              Xem chính sách <ArrowDown size={18} weight="light" />
            </a>
          </div>
        </section>

        <nav className="ownership-subnav" aria-label="Nội dung dịch vụ hậu mãi">
          <div className="section-frame">
            <a href="#care-overview">Phạm vi</a>
            <a href="#battery-warranty">Pin cao áp</a>
            <a href="#parts-warranty">Phụ tùng</a>
            <a href="#care-exclusions">Loại trừ</a>
            <a href="#care-support">Hỗ trợ</a>
          </div>
        </nav>

        <section className="policy-intro" id="care-overview">
          <div className="section-frame policy-intro__grid">
            <Reveal className="policy-intro__heading">
              <p className="eyebrow">Phạm vi bảo hành</p>
              <h2>Một nguyên tắc rõ ràng cho mọi xưởng dịch vụ.</h2>
            </Reveal>
            <Reveal className="policy-intro__lead" delay={0.08}>
              <p>
                Công việc bảo hành được thực hiện miễn phí theo điều khoản áp dụng. Khi việc sửa chữa có thể khắc phục lỗi chất lượng, vật liệu hoặc lắp ráp, chính sách không đồng nghĩa với việc thu hồi hay đổi sang một sản phẩm khác.
              </p>
              <span>Áp dụng trên toàn lãnh thổ Việt Nam</span>
            </Reveal>
          </div>

          <div className="section-frame principle-grid">
            {warrantyPrinciples.map((item) => (
              <article className="policy-card principle-card" key={item.index}>
                <span>{item.index}</span>
                <h3>{item.title}</h3>
                <p>{item.copy}</p>
                <CheckCircle size={24} weight="light" aria-hidden="true" />
              </article>
            ))}
          </div>
        </section>

        <section className="electronic-book">
          <div className="section-frame electronic-book__grid">
            <Reveal className="electronic-book__media">
              <SmartImage
                src={ownershipMedia.afterSalesConsultation}
                alt="Khách hàng được tư vấn tại xưởng dịch vụ VinFast"
              />
            </Reveal>
            <Reveal className="electronic-book__copy" delay={0.08}>
              <BookOpen size={30} weight="light" aria-hidden="true" />
              <p className="eyebrow">Sổ bảo hành điện tử</p>
              <h2>Quyền lợi đi cùng chiếc xe, không nằm trong một tập giấy.</h2>
              <p>
                Tại thời điểm bàn giao, đại lý sẽ hướng dẫn xác nhận và tra cứu Sổ bảo hành điện tử. Xe sử dụng tiêu chuẩn và xe đang hoặc từng phục vụ hoạt động thương mại được áp dụng điều kiện riêng.
              </p>
              <p className="policy-note">
                Xe đã từng dùng cho taxi, chở khách, cho thuê, đưa đón hoặc giao hàng tiếp tục theo chính sách xe dịch vụ thương mại kể cả sau khi chuyển nhượng.
              </p>
              {ownershipMedia.afterSalesBrochure && (
                <a href={ownershipMedia.afterSalesBrochure} target="_blank" rel="noreferrer">
                  Mở tài liệu chính sách gốc <ArrowUpRight size={18} weight="light" />
                </a>
              )}
            </Reveal>
          </div>
        </section>

        <section className="battery-warranty" id="battery-warranty">
          <div className="section-frame">
            <Reveal className="section-heading section-heading--wide">
              <p className="eyebrow">Pin cao áp mua theo xe mới</p>
              <h2>Thời hạn được đọc theo năm hoặc quãng đường—điều kiện nào đến trước.</h2>
            </Reveal>
            <div className="battery-warranty__grid">
              {highVoltageWarranty.map((item, index) => (
                <article className="policy-card battery-term" key={item.term}>
                  <span className="battery-term__index">0{index + 1}</span>
                  <div>
                    <strong>{item.term}</strong>
                    <em>hoặc {item.distance}</em>
                  </div>
                  <p>{item.models}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="parts-policy" id="parts-warranty">
          <div className="section-frame">
            <Reveal className="parts-policy__heading">
              <p className="eyebrow">Phụ tùng & phụ kiện</p>
              <h2>Bảo hành tiếp tục sau lần sửa chữa.</h2>
              <p>Phụ tùng thay trong bảo hành xe nhận thời hạn còn lại của xe hoặc của chính phụ tùng đó, tùy trường hợp áp dụng.</p>
            </Reveal>

            <div className="parts-bento">
              <article className="policy-card parts-bento__main">
                <span>Ô tô điện</span>
                <strong>2 năm</strong>
                <em>hoặc 40.000 km</em>
                <p>Phụ tùng chính hãng do khách hàng chi trả và được thay tại xưởng dịch vụ/nhà phân phối VinFast. Không gồm ắc quy 12V và pin cao áp.</p>
              </article>
              <article className="policy-card parts-bento__side">
                <span>Phụ kiện chính hãng</span>
                <strong>2 năm</strong>
                <em>không giới hạn km</em>
                <p>Gồm bộ sạc di động, bộ sửa lốp, thảm sàn, rèm trần, xích lốp, giá ngăn hành lý, tam giác cảnh báo và áo phản quang theo điều kiện chính sách.</p>
              </article>
              <article className="policy-card">
                <span>Móc kéo · bậc lên xuống · giá đỡ hành lý</span>
                <strong>5 năm</strong>
                <em>sử dụng tiêu chuẩn · không giới hạn km</em>
              </article>
              <article className="policy-card">
                <span>Cùng nhóm phụ kiện</span>
                <strong>3 năm</strong>
                <em>dịch vụ thương mại · VF 3, VF 7, VF 8, VF 9, VF 8 All New</em>
              </article>
              <article className="policy-card">
                <span>Lưu ý lắp đặt</span>
                <strong>Chính hãng</strong>
                <em>đúng xưởng · đủ hồ sơ</em>
                <p>Phụ tùng mua nhưng lắp bên ngoài hệ thống VinFast không được bảo hành theo chính sách này. Với phụ kiện, khách hàng cần lưu hồ sơ lắp đặt, quyết toán và hóa đơn.</p>
              </article>
            </div>
            <details className="legacy-policy-note">
              <summary>Tham chiếu phụ tùng cho các mẫu ô tô xăng VinFast</summary>
              <p>Fadil, Lux A, Lux SA và President: 12 tháng hoặc 20.000 km, tùy điều kiện nào đến trước, tính từ ngày hoàn thành sửa chữa.</p>
            </details>
          </div>
        </section>

        <section className="policy-accordion" id="care-exclusions">
          <div className="section-frame policy-accordion__grid">
            <Reveal className="policy-accordion__intro">
              <p className="eyebrow">Điều cần lưu ý</p>
              <h2>Chủ động sớm để giữ trọn quyền lợi.</h2>
              <p>Chi tiết cuối cùng luôn được đối chiếu với Sổ bảo hành đi cùng sản phẩm và ngày hiệu lực tại thời điểm mua.</p>
            </Reveal>
            <div className="policy-accordion__items">
              {exclusions.map((item, index) => (
                <details className="policy-card" key={item.title} open={index === 0}>
                  <summary><span>0{index + 1}</span>{item.title}</summary>
                  <p>{item.copy}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className="policy-faq">
          <div className="section-frame policy-faq__grid">
            <Reveal>
              <p className="eyebrow">Câu hỏi thường gặp</p>
              <h2>Tra cứu trước khi mang xe tới xưởng.</h2>
            </Reveal>
            <div>
              {questions.map((item) => (
                <details key={item.title}>
                  <summary>{item.title}<span aria-hidden="true">+</span></summary>
                  <p>{item.copy}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className="ownership-contact" id="care-support">
          <div className="section-frame ownership-contact__grid">
            <div>
              <ShieldCheck size={42} weight="light" aria-hidden="true" />
              <p className="eyebrow">Dịch vụ khách hàng</p>
              <h2>Khi cần, luôn có một điểm chạm rõ ràng.</h2>
            </div>
            <div className="ownership-contact__actions">
              <a href="tel:1900232389"><Headset size={24} weight="light" /><span><small>Hotline · nhánh 1</small><strong>1900 23 23 89</strong></span></a>
              <a href="mailto:support.vn@vinfastauto.com"><EnvelopeSimple size={24} weight="light" /><span><small>Email hỗ trợ</small><strong>support.vn@vinfastauto.com</strong></span></a>
            </div>
          </div>
        </section>

        <footer className="ownership-footer">
          <div className="section-frame">
            <strong>VINFAST</strong>
            <p>Nội dung được hệ thống lại từ brochure chính sách bảo hành do người dùng cung cấp. Điều kiện áp dụng thực tế theo Sổ bảo hành và chính sách có hiệu lực tại ngày mua.</p>
          </div>
        </footer>
      </main>
    </AppShell>
  )
}
