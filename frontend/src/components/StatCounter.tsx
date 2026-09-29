import { useInView } from '../hooks/useInView'
import { useCountUp } from '../hooks/useCountUp'

export default function StatCounter({ value, suffix = '', label }: { value: number; suffix?: string; label: string }) {
  const { ref, isInView } = useInView<HTMLDivElement>()
  const count = useCountUp(value, isInView)

  return (
    <div className="stat" ref={ref}>
      <span className="stat-value">
        {count}
        {suffix}
      </span>
      <span className="stat-label">{label}</span>
    </div>
  )
}
