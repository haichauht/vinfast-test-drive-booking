/**
 * Dấu ấn Lạc Hồng trên trang chủ.
 *
 * Đây là một chương kể về năng lực thiết kế và chế tác của VinFast, không phải bảng
 * giới thiệu sản phẩm. Ảnh xe đã được chuẩn hoá alpha; bộ xem xoay dùng duy nhất một
 * canvas và chỉ thay đổi góc khi người dùng kéo. Lạc Hồng chưa đi vào luồng đặt lịch.
 */
import { useRef } from 'react'
import { useGSAP } from '@gsap/react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { SmartImage } from '../SmartImage'
import { LacHongSpin } from './LacHongSpin'
import { lacHongDisclaimer, lacHongModels, lacHongSpin } from '../../data/lachong'

gsap.registerPlugin(useGSAP, ScrollTrigger)

const statement = 'Từ năng lực chế tác Việt đến một biểu tượng mang dấu ấn riêng.'

export function LacHongPassage() {
  const root = useRef(null)
  const [flagship, sedan] = lacHongModels

  useGSAP(
    () => {
      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      if (reduced) {
        gsap.set('.lachong-word, .lachong-figure__car, .lachong-block__copy > *, .lachong-spin', {
          opacity: 1,
          x: 0,
          y: 0,
          scale: 1,
        })
        return
      }

      gsap.fromTo(
        '.lachong-word',
        { opacity: 0.14 },
        {
          opacity: 1,
          stagger: 0.035,
          ease: 'none',
          scrollTrigger: {
            trigger: '.lachong-passage__heading',
            start: 'top 78%',
            end: 'bottom 45%',
            scrub: 0.75,
          },
        },
      )

      gsap.utils.toArray('.lachong-figure').forEach((figure) => {
        const car = figure.querySelector('.lachong-figure__car')
        gsap.fromTo(
          car,
          { xPercent: -16, scale: 0.9, opacity: 0 },
          {
            xPercent: 0,
            scale: 1,
            opacity: 1,
            ease: 'none',
            scrollTrigger: { trigger: figure, start: 'top 92%', end: 'center 56%', scrub: 0.9 },
          },
        )
      })

      gsap.utils.toArray('.lachong-block__copy').forEach((copy) => {
        gsap.fromTo(
          copy.children,
          { y: 30, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 0.9,
            stagger: 0.075,
            ease: 'power4.out',
            scrollTrigger: { trigger: copy, start: 'top 84%', once: true },
          },
        )
      })

      gsap.fromTo(
        '.lachong-spin',
        { y: 70, scale: 0.94, opacity: 0 },
        {
          y: 0,
          scale: 1,
          opacity: 1,
          duration: 1.25,
          ease: 'power4.out',
          scrollTrigger: { trigger: '.lachong-spin-block', start: 'top 82%', once: true },
        },
      )
    },
    { scope: root },
  )

  const renderMeta = (items) => (
    <dl className="lachong-block__meta">
      {items.map((item) => (
        <div key={item.label}>
          <dt>{item.label}</dt>
          <dd>{item.value}</dd>
        </div>
      ))}
    </dl>
  )

  return (
    <section className="lachong-passage" id="lac-hong" ref={root} aria-labelledby="lachong-title">
      <div className="section-frame">
        <div className="lachong-passage__heading">
          <p className="eyebrow">Dấu ấn VinFast</p>
          <h2 id="lachong-title" aria-label={statement}>
            {statement.split(' ').map((word, index) => (
              <span className="lachong-word" aria-hidden="true" key={`${word}-${index}`}>{word} </span>
            ))}
          </h2>
          <p>
            Lạc Hồng là một lát cắt trong hành trình VinFast làm chủ thiết kế, công nghệ
            và năng lực chế tác — nơi bản sắc Việt được chuyển thành một ngôn ngữ có thể nhìn thấy.
          </p>
        </div>
      </div>

      <div className="section-frame lachong-block lachong-block--flagship">
        <figure className="lachong-figure">
          <SmartImage className="lachong-figure__car" src={flagship.image} alt={`${flagship.name}, dấu ấn chế tác của VinFast`} fit="contain" />
        </figure>
        <div className="lachong-block__copy">
          <span className="lachong-block__narrative">{flagship.narrative}</span>
          <small>{flagship.name}</small>
          <h3>{flagship.headline}</h3>
          <p>{flagship.copy}</p>
          {renderMeta(flagship.meta)}
        </div>
      </div>

      <div className="lachong-spin-chapter">
        <div className="section-frame lachong-spin-block">
          <div className="lachong-spin-block__intro">
            <div>
              <p className="eyebrow">Góc nhìn tương tác</p>
              <h3>Chạm vào một góc nhìn của năng lực Việt.</h3>
            </div>
            <p>Giữ và kéo trực tiếp trên xe. Góc nhìn chỉ chuyển động theo tay bạn.</p>
          </div>
          <LacHongSpin frames={lacHongSpin.frames} name={lacHongSpin.name} />
        </div>
      </div>

      <div className="section-frame lachong-block lachong-block--sedan">
        <div className="lachong-block__copy">
          <span className="lachong-block__narrative">{sedan.narrative}</span>
          <small>{sedan.name}</small>
          <h3>{sedan.headline}</h3>
          <p>{sedan.copy}</p>
          {renderMeta(sedan.meta)}
        </div>
        <figure className="lachong-figure">
          <SmartImage className="lachong-figure__car" src={sedan.image} alt={`${sedan.name}, ngôn ngữ thiết kế VinFast`} fit="contain" />
        </figure>
      </div>

      <div className="section-frame">
        <p className="lachong-disclaimer"><span aria-hidden="true">*</span> {lacHongDisclaimer}</p>
      </div>
    </section>
  )
}
