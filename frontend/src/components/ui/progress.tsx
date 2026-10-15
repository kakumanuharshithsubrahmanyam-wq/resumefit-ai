import { cn } from '@/lib/utils'

type ProgressProps = {
  value: number
  className?: string
}

function Progress({ value, className }: ProgressProps) {
  const clamped = Math.min(100, Math.max(0, value))
  return (
    <div
      className={cn(
        'relative h-2 w-full overflow-hidden rounded-full bg-secondary',
        className,
      )}
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={clamped}
    >
      <div
        className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-300 ease-out"
        style={{ width: `${clamped}%` }}
      />
    </div>
  )
}

export { Progress }
