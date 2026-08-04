import { useRef } from 'react'
import { useGSAP } from '@gsap/react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(useGSAP, ScrollTrigger)

export function Reveal({
  as: Tag = 'div',
  children,
  className = '',
  delay = 0,
  y = 56,
}) {
  const root = useRef(null)

  useGSAP(
    () => {
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        gsap.set(root.current, { opacity: 1, y: 0 })
        return
      }

      gsap.fromTo(
        root.current,
        { opacity: 0, y, filter: 'blur(10px)' },
        {
          opacity: 1,
          y: 0,
          filter: 'blur(0px)',
          duration: 1.05,
          delay,
          ease: 'power4.out',
          scrollTrigger: {
            trigger: root.current,
            start: 'top 88%',
            once: true,
          },
        },
      )
    },
    { scope: root, dependencies: [delay, y] },
  )

  return (
    <Tag ref={root} className={`reveal-shell ${className}`.trim()}>
      {children}
    </Tag>
  )
}
