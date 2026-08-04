import { useState } from 'react'
import { ImageBroken } from '@phosphor-icons/react'

export function SmartImage({ className = '', alt, src, eager = false, ...props }) {
  const [status, setStatus] = useState(src ? 'loading' : 'error')

  return (
    <span className={`smart-image smart-image--${status} ${className}`.trim()}>
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
          onLoad={() => setStatus('loaded')}
          onError={() => setStatus('error')}
          {...props}
        />
      )}
    </span>
  )
}
