/**
 * Post-confirmation product film.
 *
 * Integration boundary:
 * - Receives the already-confirmed vehicle and an `onComplete` callback.
 * - Does not create, mutate or retry a booking.
 * - Backend state remains owned by BookingPage; this component only delays the
 *   success document until the visual sequence is complete.
 */
import { useEffect, useRef, useState } from 'react'
import { useGSAP } from '@gsap/react'
import gsap from 'gsap'
import { SmartImage } from './SmartImage'
import { preloadVehicle3dRuntime } from './Vehicle3DExperience'
import { getVehicle3dModel } from '../data/vehicle3d'
import { vehicleImage } from '../media/assets'
import './BookingSuccessCinematic.css'

const vinfastWordmark = vehicleImage('Vinfast-logo-new_NO_Tagline -2D-Horizontal black.png')

const splitOrbit = (orbit) => {
  const [azimuth, ...rest] = orbit.trim().split(/\s+/)
  return { azimuth: Number.parseFloat(azimuth), suffix: rest.join(' ') }
}

const nearestEquivalentAngle = (from, to) => {
  const delta = ((((to - from) + 180) % 360) + 360) % 360 - 180
  return from + delta
}

const applyModelFinish = (viewer, config) => {
  const finish = config?.paint
  const material = finish && viewer?.model?.getMaterialByName?.(finish.materialName)
  const pbr = material?.pbrMetallicRoughness
  if (!pbr) return
  if (finish.removeBaseColorTexture) pbr.baseColorTexture?.setTexture(null)
  pbr.setBaseColorFactor(finish.baseColor)
  pbr.setMetallicFactor(finish.metallicFactor)
  pbr.setRoughnessFactor(finish.roughnessFactor)
}

function CinematicModel({ car, config, viewerRef, onReady, onFailure }) {
  const [runtimeReady, setRuntimeReady] = useState(false)

  useEffect(() => {
    let active = true
    preloadVehicle3dRuntime()
      .then(() => { if (active) setRuntimeReady(true) })
      .catch(() => { if (active) onFailure() })
    return () => { active = false }
  }, [onFailure])

  useEffect(() => {
    const viewer = viewerRef.current
    if (!viewer || !runtimeReady) return undefined
    const handleLoad = () => {
      applyModelFinish(viewer, config)
      onReady()
    }
    const handleError = () => onFailure()
    viewer.addEventListener('load', handleLoad)
    viewer.addEventListener('error', handleError)
    if (viewer.loaded) handleLoad()
    return () => {
      viewer.removeEventListener('load', handleLoad)
      viewer.removeEventListener('error', handleError)
    }
  }, [config, onFailure, onReady, runtimeReady, viewerRef])

  return (
    <model-viewer
      ref={viewerRef}
      src={runtimeReady ? config.src : undefined}
      alt={`Mô hình 3D ${car.name} trong chuyển cảnh xác nhận lịch`}
      loading="eager"
      reveal="auto"
      interaction-prompt="none"
      camera-orbit={config.sideOrbit}
      field-of-view={config.fieldOfView}
      shadow-intensity="0"
      exposure="0.76"
      environment-image="neutral"
      tone-mapping="aces"
    />
  )
}

const createSeededRandom = (text) => {
  let state = [...text].reduce((value, char) => ((value * 31) + char.charCodeAt(0)) >>> 0, 2166136261)
  return () => {
    state = ((state * 1664525) + 1013904223) >>> 0
    return state / 4294967296
  }
}

/** A small deterministic particle renderer keeps smoke physical and repeatable. */
const useTyreSmoke = (canvasRef, rootRef, vehicleRef, controlRef, vehicleId) => {
  useEffect(() => {
    const canvas = canvasRef.current
    const root = rootRef.current
    if (!canvas || !root) return undefined

    const context = canvas.getContext('2d', { alpha: true })
    if (!context) return undefined

    const random = createSeededRandom(vehicleId || 'vinfast')
    const particles = []
    const tyreTrails = [[], []]
    const sprite = document.createElement('canvas')
    const spriteSize = 128
    sprite.width = spriteSize
    sprite.height = spriteSize
    const spriteContext = sprite.getContext('2d')
    const spriteGradient = spriteContext.createRadialGradient(64, 64, 3, 64, 64, 61)
    spriteGradient.addColorStop(0, 'rgba(214, 218, 220, 0.32)')
    spriteGradient.addColorStop(0.42, 'rgba(151, 157, 161, 0.17)')
    spriteGradient.addColorStop(1, 'rgba(74, 78, 82, 0)')
    spriteContext.fillStyle = spriteGradient
    spriteContext.fillRect(0, 0, spriteSize, spriteSize)

    let width = 0
    let height = 0
    let dpr = 1
    let frame = 0
    let previousTime = performance.now()
    let spawnCarry = 0
    let trailCarry = 0

    const resize = () => {
      const rect = root.getBoundingClientRect()
      width = rect.width
      height = rect.height
      dpr = Math.min(window.devicePixelRatio || 1, 1.5)
      canvas.width = Math.round(width * dpr)
      canvas.height = Math.round(height * dpr)
      canvas.style.width = `${width}px`
      canvas.style.height = `${height}px`
      context.setTransform(dpr, 0, 0, dpr, 0, 0)
    }

    const getContactPoints = () => {
      const control = controlRef.current
      const rearView = control.rearMix
      const rect = vehicleRef.current?.getBoundingClientRect()
      if (!rect) return [{ x: width * 0.5, y: height * 0.68 }, { x: width * 0.5, y: height * 0.68 }]

      // Side profile points to the right: its rear axle sits left of centre.
      // As cameraOrbit approaches rear view, the one visible contact patch
      // separates into the two rear tyres. Every coordinate comes from the
      // transformed vehicle rect, so smoke cannot drift away from the car.
      const sideX = rect.left + (rect.width * 0.355)
      const rearCenterX = rect.left + (rect.width * 0.5)
      const centerX = sideX + ((rearCenterX - sideX) * rearView)
      const separation = rect.width * 0.082 * rearView
      const y = rect.top + (rect.height * (0.705 + (rearView * 0.018)))
      return [{ x: centerX - separation, y }, { x: centerX + separation, y }]
    }

    const spawnParticle = () => {
      const control = controlRef.current
      const rearView = control.rearMix
      const contacts = getContactPoints()
      const contact = contacts[random() > 0.5 ? 1 : 0]
      const size = 26 + (random() * 54)
      particles.push({
        x: contact.x + ((random() - 0.5) * Math.min(width * 0.026, 30)),
        y: contact.y + ((random() - 0.5) * Math.min(height * 0.018, 15)),
        vx: (-34 - (random() * 58)) * (1 - (rearView * 0.72)),
        vy: -12 - (random() * 30),
        size,
        growth: 22 + (random() * 30),
        life: 0,
        ttl: 0.78 + (random() * 0.62),
        opacity: 0.34 + (random() * 0.3),
        rotation: random() * Math.PI * 2,
        spin: (random() - 0.5) * 0.8,
      })
    }

    const render = (time) => {
      const delta = Math.min((time - previousTime) / 1000, 0.035)
      previousTime = time
      context.clearRect(0, 0, width, height)

      const intensity = controlRef.current.intensity
      spawnCarry += intensity * delta * 88
      while (spawnCarry >= 1 && particles.length < 110) {
        spawnParticle()
        spawnCarry -= 1
      }

      const skid = controlRef.current.skid
      trailCarry += skid * delta * 56
      while (trailCarry >= 1) {
        const contacts = getContactPoints()
        contacts.forEach((point, index) => tyreTrails[index].push({ ...point, life: 0 }))
        trailCarry -= 1
      }

      tyreTrails.forEach((trail) => {
        for (let index = trail.length - 1; index >= 0; index -= 1) {
          trail[index].life += delta
          if (trail[index].life > 1.65) trail.splice(index, 1)
        }
        if (trail.length < 2) return
        context.beginPath()
        trail.forEach((point, index) => {
          if (index === 0) context.moveTo(point.x, point.y)
          else context.lineTo(point.x, point.y)
        })
        context.lineWidth = 1
        context.strokeStyle = `rgba(255, 255, 255, ${0.075 * Math.min(skid + 0.2, 1)})`
        context.stroke()
      })

      for (let index = particles.length - 1; index >= 0; index -= 1) {
        const particle = particles[index]
        particle.life += delta
        if (particle.life >= particle.ttl) {
          particles.splice(index, 1)
          continue
        }
        const progress = particle.life / particle.ttl
        particle.x += particle.vx * delta
        particle.y += particle.vy * delta
        particle.size += particle.growth * delta
        particle.rotation += particle.spin * delta
        const alpha = Math.sin(progress * Math.PI) * particle.opacity
        context.save()
        context.globalAlpha = alpha
        context.translate(particle.x, particle.y)
        context.rotate(particle.rotation)
        context.drawImage(sprite, -particle.size / 2, -particle.size / 2, particle.size, particle.size)
        context.restore()
      }

      frame = window.requestAnimationFrame(render)
    }

    resize()
    window.addEventListener('resize', resize)
    frame = window.requestAnimationFrame(render)
    return () => {
      window.cancelAnimationFrame(frame)
      window.removeEventListener('resize', resize)
    }
  }, [canvasRef, controlRef, rootRef, vehicleId, vehicleRef])
}

export function BookingSuccessCinematic({ car, onComplete }) {
  const config = getVehicle3dModel(car?.id)
  const root = useRef(null)
  const viewer = useRef(null)
  const vehicle = useRef(null)
  const canvas = useRef(null)
  const smoke = useRef({ intensity: 0, rearMix: 0, skid: 0 })
  const [modelReady, setModelReady] = useState(!config)
  const [modelFailed, setModelFailed] = useState(false)

  useTyreSmoke(canvas, root, vehicle, smoke, car?.id)

  useEffect(() => {
    setModelReady(!config)
    setModelFailed(false)
  }, [car?.id, config])

  useEffect(() => {
    if (!config || modelReady || modelFailed) return undefined
    const timeout = window.setTimeout(() => setModelFailed(true), 6000)
    return () => window.clearTimeout(timeout)
  }, [config, modelFailed, modelReady])

  useGSAP(
    () => {
      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      if (reduced) {
        gsap.set(root.current, { autoAlpha: 1 })
        const timer = window.setTimeout(onComplete, 260)
        return () => window.clearTimeout(timer)
      }

      if (config && !modelFailed && !modelReady) return undefined

      const movingVehicle = vehicle.current
      const brandPrelude = root.current?.querySelector('.booking-film__brand')
      const air = root.current?.querySelector('.booking-film__air')
      const airLines = root.current?.querySelectorAll('.booking-film__air span')
      const confirmation = root.current?.querySelector('.booking-film__confirmation')
      const confirmationRule = confirmation?.querySelector('i')
      if (!movingVehicle) return undefined

      const sideOrbit = config ? splitOrbit(config.sideOrbit) : null
      const rearOrbit = config ? splitOrbit(config.rearOrbit) : null
      const camera = sideOrbit ? { azimuth: sideOrbit.azimuth } : null
      const rearAzimuth = sideOrbit && rearOrbit
        ? nearestEquivalentAngle(sideOrbit.azimuth, rearOrbit.azimuth)
        : 0
      const light = { exposure: 0.72 }

      if (viewer.current && config) {
        viewer.current.cameraOrbit = config.sideOrbit
        viewer.current.exposure = light.exposure
        viewer.current.jumpCameraToGoal?.()
      }

      gsap.set(root.current, { autoAlpha: 0 })
      const enterX = -((root.current.clientWidth + movingVehicle.offsetWidth) / 2 + 48)
      gsap.set(movingVehicle, { x: enterX, y: 0, scale: 0.7, rotateZ: 0.18, opacity: 1, filter: 'blur(1.4px)' })
      gsap.set(brandPrelude, { autoAlpha: 0, scale: 0.82 })
      gsap.set(airLines, { scaleX: 0.08, opacity: 0, transformOrigin: 'right center' })
      gsap.set(confirmation, { opacity: 0 })

      const updateCamera = () => {
        if (!viewer.current || !camera || !rearOrbit) return
        viewer.current.cameraOrbit = `${camera.azimuth}deg ${rearOrbit.suffix}`
        viewer.current.jumpCameraToGoal?.()
      }
      const updateExposure = () => {
        if (viewer.current) viewer.current.exposure = light.exposure
      }

      const timeline = gsap.timeline({ defaults: { ease: 'power3.inOut' } })
      timeline
        // The interface first resolves into absolute black. The approved
        // VinFast wordmark appears front-facing, holds briefly, then clears
        // the stage before the vehicle enters. It never spins or flips.
        .call(() => { root.current.dataset.phase = 'blackout' })
        .to(root.current, { autoAlpha: 1, duration: 0.3, ease: 'power2.out' })
        .call(() => { root.current.dataset.phase = 'brand-prelude' })
        .to(brandPrelude, { autoAlpha: 1, scale: 1, duration: 0.54, ease: 'power3.out' })
        .to({}, { duration: 0.72 })
        .to(brandPrelude, { autoAlpha: 0, scale: 0.96, filter: 'blur(5px)', duration: 0.36, ease: 'power2.in' })
        .set(brandPrelude, { visibility: 'hidden' })
        .addLabel('vehicle-approach')
        // Side profile enters with acceleration. Air compression is tied to
        // this exact interval and stops before the drift begins.
        .call(() => { root.current.dataset.phase = 'side-approach' })
        .to(movingVehicle, { x: -132, scale: 0.76, filter: 'blur(0.55px)', duration: 1.48, ease: 'power2.in' })
        .to(movingVehicle, { x: 0, scale: 0.79, filter: 'blur(0)', duration: 0.48, ease: 'power3.out' })
        .to(air, { opacity: 1, duration: 0.12 }, 'vehicle-approach+=0.06')
        .to(airLines, { scaleX: 1, opacity: 0.42, duration: 0.62, stagger: 0.055, ease: 'power2.in' }, 'vehicle-approach+=0.1')
        .to(airLines, { scaleX: 0.2, opacity: 0, duration: 0.5, stagger: 0.035, ease: 'power3.out' }, 'vehicle-approach+=1.1')
        .to(air, { opacity: 0, duration: 0.2 }, 'vehicle-approach+=1.62')
        .to(light, { exposure: config?.exposure || 1.04, duration: 1.36, ease: 'power1.inOut', onUpdate: updateExposure }, 'vehicle-approach+=0.14')
        // Load transfers forward, then the vehicle rotates through a rear
        // three-quarter angle. Tyre smoke and skid marks begin at peak load.
        .call(() => { root.current.dataset.phase = 'drift' })
        .to(movingVehicle, { x: 44, y: 14, rotateZ: -1.25, scaleX: 1.018, scaleY: 0.982, duration: 0.28, ease: 'power2.out' })
        .to(smoke.current, { intensity: 1, skid: 1, duration: 0.16, ease: 'power2.out' }, '<')
        .to(camera || {}, { azimuth: rearAzimuth, duration: config ? 1.12 : 0, ease: 'power2.inOut', onUpdate: updateCamera }, '<')
        .to(smoke.current, { rearMix: 1, duration: 0.82, ease: 'power1.inOut' }, '<+=0.14')
        .to(movingVehicle, { x: 0, y: 0, rotateZ: 0, scaleX: 1, scaleY: 1, duration: 0.86, ease: 'power3.out' }, '<+=0.18')
        .to(smoke.current, { intensity: 0, skid: 0, duration: 0.92, ease: 'power2.out' }, '<+=0.24')
        .to({}, { duration: 0.38 })
        // Rear view now owns the centre. It remains sharp while accelerating
        // into depth; opacity falls only in the last metres.
        .call(() => { root.current.dataset.phase = 'rear-retreat' })
        .to(movingVehicle, { x: 0, scale: 0.055, y: -30, duration: 1.72, ease: 'expo.in' })
        .to(light, { exposure: 0.48, duration: 1.25, ease: 'power2.in', onUpdate: updateExposure }, '<')
        .to(movingVehicle, { opacity: 0, duration: 0.28, ease: 'power1.in' }, '-=0.22')
        .to(canvas.current, { opacity: 0, duration: 0.38 }, '-=0.34')
        .call(() => { root.current.dataset.phase = 'confirmed' })
        .to(confirmation, { opacity: 1, duration: 0.42, ease: 'power2.out' })
        .to(confirmationRule, { scaleX: 1, duration: 0.38, ease: 'power3.out' }, '<+=0.04')
        .to({}, { duration: 0.46 })
        .to(confirmation, { opacity: 0, y: -8, duration: 0.3, ease: 'power2.in' })
        .to(root.current, { autoAlpha: 0, duration: 0.42, ease: 'power2.inOut' })
        .call(onComplete)

      return () => timeline.kill()
    },
    { scope: root, dependencies: [car?.id, config, modelFailed, modelReady, onComplete] },
  )

  if (!car) return null

  return (
    <div className="booking-film" ref={root} role="status" aria-live="polite" aria-label="Đang hoàn tất lịch lái thử">
      <div className="booking-film__brand" aria-hidden="true">
        <img className="booking-film__brand-mark" src={vinfastWordmark} alt="" />
      </div>
      <div className="booking-film__air" aria-hidden="true"><span /><span /><span /><span /></div>
      <canvas className="booking-film__smoke" ref={canvas} aria-hidden="true" />
      <div className="booking-film__rig">
        <div className="booking-film__vehicle" ref={vehicle}>
          {config && !modelFailed ? (
            <CinematicModel
              car={car}
              config={config}
              viewerRef={viewer}
              onReady={() => setModelReady(true)}
              onFailure={() => {
                setModelFailed(true)
                setModelReady(true)
              }}
            />
          ) : (
            <SmartImage className="booking-film__fallback" src={car.motionImage || car.intro} alt="" aria-hidden="true" fit="contain" />
          )}
        </div>
      </div>
      <div className="booking-film__confirmation" aria-hidden="true">
        <i />
        <strong>Lịch lái thử đã được xác nhận.</strong>
      </div>
    </div>
  )
}
