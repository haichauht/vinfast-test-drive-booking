/**
 * Một bề mặt canvas duy nhất cho trải nghiệm xoay Lạc Hồng.
 *
 * Nguồn hiện chưa có GLB/GLTF, nên canvas nội suy 5 góc render đã được tách alpha.
 * Không render thumbnail, không autoplay và không để lộ từng lớp ảnh trong DOM. Khi backend
 * cung cấp model 3D thật, có thể thay canvas này bằng model-viewer mà không đổi bố cục ngoài.
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { HandPointing, SpinnerGap } from '@phosphor-icons/react'

const DRAG_PER_FRAME = 150

const normalizedPosition = (value, total) => ((value % total) + total) % total

export function LacHongSpin({ frames, name }) {
  const canvasRef = useRef(null)
  const imagesRef = useRef([])
  const positionRef = useRef(0)
  const dragRef = useRef(null)
  const paintFrameRef = useRef(0)
  const [ready, setReady] = useState(false)
  const [touched, setTouched] = useState(false)

  const paint = useCallback(() => {
    const canvas = canvasRef.current
    const images = imagesRef.current
    if (!canvas || images.length !== frames.length) return

    const bounds = canvas.getBoundingClientRect()
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const width = Math.max(1, Math.round(bounds.width))
    const height = Math.max(1, Math.round(bounds.height))

    if (canvas.width !== Math.round(width * dpr) || canvas.height !== Math.round(height * dpr)) {
      canvas.width = Math.round(width * dpr)
      canvas.height = Math.round(height * dpr)
    }

    const context = canvas.getContext('2d')
    context.setTransform(dpr, 0, 0, dpr, 0, 0)
    context.clearRect(0, 0, width, height)

    const ambience = context.createRadialGradient(
      width * 0.52,
      height * 0.45,
      width * 0.04,
      width * 0.52,
      height * 0.45,
      width * 0.72,
    )
    ambience.addColorStop(0, '#273039')
    ambience.addColorStop(0.48, '#141a20')
    ambience.addColorStop(1, '#080b0f')
    context.fillStyle = ambience
    context.fillRect(0, 0, width, height)

    const floor = context.createRadialGradient(
      width * 0.5,
      height * 0.79,
      0,
      width * 0.5,
      height * 0.79,
      width * 0.38,
    )
    floor.addColorStop(0, 'rgba(0, 0, 0, 0.58)')
    floor.addColorStop(1, 'rgba(0, 0, 0, 0)')
    context.save()
    context.scale(1, 0.24)
    context.fillStyle = floor
    context.fillRect(width * 0.1, height * 2.85, width * 0.8, height)
    context.restore()

    const position = normalizedPosition(positionRef.current, images.length)
    const currentIndex = Math.floor(position)
    const nextIndex = (currentIndex + 1) % images.length
    const rawMix = position - currentIndex
    const mix = rawMix * rawMix * (3 - 2 * rawMix)

    const drawImage = (image, alpha) => {
      const scale = Math.min((width * 0.9) / image.naturalWidth, (height * 0.78) / image.naturalHeight)
      const drawWidth = image.naturalWidth * scale
      const drawHeight = image.naturalHeight * scale
      const x = (width - drawWidth) / 2
      const y = height * 0.49 - drawHeight / 2
      context.save()
      context.globalAlpha = alpha
      context.drawImage(image, x, y, drawWidth, drawHeight)
      context.restore()
    }

    drawImage(images[currentIndex], 1 - mix)
    if (mix > 0.001) drawImage(images[nextIndex], mix)
  }, [frames.length])

  const queuePaint = useCallback(() => {
    window.cancelAnimationFrame(paintFrameRef.current)
    paintFrameRef.current = window.requestAnimationFrame(paint)
  }, [paint])

  useEffect(() => {
    let cancelled = false
    const sources = frames.map((src) => new Promise((resolve, reject) => {
      const image = new Image()
      image.decoding = 'async'
      image.onload = () => resolve(image)
      image.onerror = reject
      image.src = src
    }))

    Promise.all(sources).then((images) => {
      if (cancelled) return
      imagesRef.current = images
      setReady(true)
      queuePaint()
    }).catch(() => {
      if (!cancelled) setReady(false)
    })

    const observer = new ResizeObserver(queuePaint)
    if (canvasRef.current) observer.observe(canvasRef.current)

    return () => {
      cancelled = true
      observer.disconnect()
      window.cancelAnimationFrame(paintFrameRef.current)
    }
  }, [frames, queuePaint])

  const onPointerDown = (event) => {
    event.currentTarget.setPointerCapture(event.pointerId)
    dragRef.current = { pointerId: event.pointerId, x: event.clientX, position: positionRef.current }
    setTouched(true)
  }

  const onPointerMove = (event) => {
    const drag = dragRef.current
    if (!drag || drag.pointerId !== event.pointerId) return
    positionRef.current = drag.position + (event.clientX - drag.x) / DRAG_PER_FRAME
    queuePaint()
  }

  const endPointer = (event) => {
    if (dragRef.current?.pointerId !== event.pointerId) return
    positionRef.current = Math.round(positionRef.current)
    dragRef.current = null
    queuePaint()
  }

  const onKeyDown = (event) => {
    const step = event.key === 'ArrowLeft' ? -1 : event.key === 'ArrowRight' ? 1 : 0
    if (!step) return
    event.preventDefault()
    positionRef.current = Math.round(positionRef.current) + step
    setTouched(true)
    queuePaint()
  }

  return (
    <div className={`lachong-spin ${ready ? 'is-ready' : 'is-loading'}`}>
      <div
        className="lachong-spin__viewport"
        role="img"
        tabIndex={0}
        aria-label={`Góc nhìn xoay của ${name}. Kéo ngang trên xe hoặc dùng phím mũi tên trái phải để xoay.`}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endPointer}
        onPointerCancel={endPointer}
        onKeyDown={onKeyDown}
      >
        <canvas ref={canvasRef} className="lachong-spin__canvas" aria-hidden="true" />
        {!ready && (
          <span className="lachong-spin__loading" aria-live="polite">
            <SpinnerGap size={20} weight="light" />
            Đang dựng góc nhìn
          </span>
        )}
        {ready && !touched && (
          <span className="lachong-spin__hint" aria-hidden="true">
            <HandPointing size={18} weight="light" />
            Giữ và kéo trực tiếp trên xe
          </span>
        )}
        <span className="lachong-spin__orbit" aria-hidden="true" />
      </div>
    </div>
  )
}
