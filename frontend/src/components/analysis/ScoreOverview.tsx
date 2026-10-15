import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Target } from 'lucide-react'

import { categoryLabel } from '@/lib/findings-utils'
import type { ScoringBreakdown } from '@/types/api'

type ScoreOverviewProps = {
  scoring: ScoringBreakdown
}

function ScoreCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 text-3xl font-semibold text-indigo-600 dark:text-indigo-300">
        {value.toFixed(1)}%
      </p>
    </div>
  )
}

export function ScoreOverview({ scoring }: ScoreOverviewProps) {
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-3">
        <ScoreCard label="Overall alignment" value={scoring.overall_alignment} />
        <ScoreCard label="Required coverage" value={scoring.required_skill_coverage} />
        <ScoreCard label="Preferred coverage" value={scoring.preferred_skill_coverage} />
      </div>

      <Alert>
        <Target className="size-4" aria-hidden="true" />
        <AlertTitle>What this score means</AlertTitle>
        <AlertDescription className="space-y-2">
          <p>{scoring.disclaimer}</p>
          <p className="text-xs text-muted-foreground">{scoring.methodology}</p>
        </AlertDescription>
      </Alert>

      <div className="grid gap-2 sm:grid-cols-2">
        {scoring.category_scores
          .filter((item) => item.total > 0)
          .map((item) => (
            <div key={item.category} className="rounded-md border bg-muted/20 p-3 text-sm">
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium">{categoryLabel(item.category)}</span>
                <span>{item.score.toFixed(1)}%</span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {item.matched} matched · {item.partial} partial · {item.missing} missing ·{' '}
                {item.uncertain} uncertain
              </p>
            </div>
          ))}
      </div>
    </div>
  )
}
