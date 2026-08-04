import { ArrowRight, ArrowUpRight } from '@phosphor-icons/react'
import { Link } from 'react-router-dom'

export function IslandButton({
  to,
  children,
  variant = 'dark',
  external = false,
  className = '',
  icon = 'right',
  ...props
}) {
  const content = (
    <>
      <span>{children}</span>
      <span className="island-button__icon" aria-hidden="true">
        {icon === 'up' ? (
          <ArrowUpRight size={16} weight="light" />
        ) : (
          <ArrowRight size={16} weight="light" />
        )}
      </span>
    </>
  )

  const classes = `island-button island-button--${variant} ${className}`.trim()

  if (to && !external) {
    return (
      <Link className={classes} to={to} {...props}>
        {content}
      </Link>
    )
  }

  if (to && external) {
    return (
      <a className={classes} href={to} target="_blank" rel="noreferrer" {...props}>
        {content}
      </a>
    )
  }

  return (
    <button className={classes} type="button" {...props}>
      {content}
    </button>
  )
}
