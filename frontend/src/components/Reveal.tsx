import type { CSSProperties, ReactNode } from 'react'
import { useInView } from '../hooks/useInView'
import './Reveal.css'

export default function Reveal({
  children,
  delay = 0,
  className = '',
}: {
  children: ReactNode
  delay?: number
  className?: string
}) {
  const { ref, isInView } = useInView<HTMLDivElement>()
  const style: CSSProperties = delay ? { transitionDelay: `${delay}ms` } : {}

  return (
    <div ref={ref} className={`reveal ${isInView ? 'reveal-visible' : ''} ${className}`} style={style}>
      {children}
    </div>
  )
}
