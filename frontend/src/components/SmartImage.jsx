import { useState } from 'react'
import { ImageBroken } from '@phosphor-icons/react'

export function SmartImage({
  className = '',
  alt,
  src,
  eager = false,
  fit,
  focalPoint,
  aspectRatio,
  style,
  ...props
}) {
  const [loadedSrc, setLoadedSrc] = useState('')
  const [failedSrc, setFailedSrc] = useState('')
  const status = !src
    ? 'error'
    : failedSrc === src
      ? 'error'
      : loadedSrc === src
        ? 'loaded'
        : 'loading'

  return (
    <span
      className={`smart-image smart-image--${status} ${className}`.trim()}
      style={{ ...style, ...(aspectRatio ? { aspectRatio } : {}) }}
    >
      {status === 'loading' && <span className="smart-image__skeleton" aria-hidden="true" />}
      {status === 'error' && (
        <span className="smart-image__error" role="img" aria-label={`Không tải được ảnh: ${alt}`}>
          <ImageBroken size={28} weight="light" aria-hidden="true" />
          <span>Ảnh đang được cập nhật</span>
        </span>
      )}
      {src && (
        <img
          src={src}
          alt={alt}
          loading={eager ? 'eager' : 'lazy'}
          style={{
            ...(fit ? { objectFit: fit } : {}),
            ...(focalPoint ? { objectPosition: focalPoint } : {}),
          }}
          onLoad={() => {
            setFailedSrc('')
            setLoadedSrc(src)
          }}
          onError={() => {
            setLoadedSrc('')
            setFailedSrc(src)
          }}
          {...props}
        />
      )}
    </span>
  )
}
