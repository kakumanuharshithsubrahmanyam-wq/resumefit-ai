import { AlertTriangle, CheckCircle2, FileSearch, Sparkles } from 'lucide-react'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import type { ATSCompatibilityResult } from '@/types/api'

type AtsCompatibilityPanelProps = {
  ats: ATSCompatibilityResult | null | undefined
}

function impactClass(impact: string) {
  if (impact === 'high') return 'text-destructive'
  if (impact === 'medium') return 'text-amber-700 dark:text-amber-400'
  return 'text-muted-foreground'
}

export function AtsCompatibilityPanel({ ats }: AtsCompatibilityPanelProps) {
  if (!ats) {
    return (
      <Alert>
        <FileSearch className="size-4" aria-hidden="true" />
        <AlertTitle>Estimated ATS Compatibility unavailable</AlertTitle>
        <AlertDescription>
          This analysis was saved before ATS scoring was added. Run a new analysis to generate an
          estimate.
        </AlertDescription>
      </Alert>
    )
  }

  if (ats.status === 'insufficient_data') {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="size-4" aria-hidden="true" />
        <AlertTitle>Insufficient data for ATS estimate</AlertTitle>
        <AlertDescription>
          {ats.improvement_opportunities[0] ??
            'Upload a resume with more extractable text to calculate ATS compatibility.'}
        </AlertDescription>
      </Alert>
    )
  }

  if (ats.status === 'unavailable' || ats.overall_score == null) {
    return (
      <Alert>
        <AlertTriangle className="size-4" aria-hidden="true" />
        <AlertTitle>ATS estimate unavailable</AlertTitle>
        <AlertDescription>
          {ats.improvement_opportunities[0] ??
            'Could not produce a reliable ATS compatibility estimate from the available data.'}
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg border bg-card p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">{ats.label}</p>
          <p className="mt-1 text-3xl font-semibold text-emerald-700 dark:text-emerald-300">
            {ats.overall_score.toFixed(1)}%
          </p>
        </div>
        <div className="rounded-lg border bg-muted/20 p-4 text-sm text-muted-foreground">
          <p>{ats.disclaimer}</p>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-sm font-semibold">Component breakdown</h3>
        {ats.components.map((component) => (
          <div key={component.id} className="space-y-1 rounded-md border p-3">
            <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
              <span className="font-medium">{component.label}</span>
              <span className="text-muted-foreground">
                {component.available && component.score != null
                  ? `${component.score.toFixed(1)}% · weight ${(component.effective_weight * 100).toFixed(0)}%`
                  : 'Unavailable'}
              </span>
            </div>
            {component.available && component.score != null && (
              <Progress value={component.score} className="h-2" />
            )}
            <p className="text-xs text-muted-foreground">{component.explanation}</p>
          </div>
        ))}
      </div>

      {ats.positive_signals.length > 0 && (
        <div className="space-y-2">
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <CheckCircle2 className="size-4 text-emerald-600" aria-hidden="true" />
            Positive signals
          </h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
            {ats.positive_signals.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {(ats.structural_warnings.length > 0 || ats.parsing_warnings.length > 0) && (
        <div className="space-y-2">
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <AlertTriangle className="size-4 text-amber-600" aria-hidden="true" />
            Structure & parsing warnings
          </h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
            {[...ats.structural_warnings, ...ats.parsing_warnings].map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {ats.missing_keywords.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold">Missing job-description terms</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
            {ats.missing_keywords.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {ats.recommended_fixes.length > 0 && (
        <div className="space-y-2">
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <Sparkles className="size-4" aria-hidden="true" />
            Prioritized fixes
          </h3>
          <ol className="space-y-2 text-sm">
            {ats.recommended_fixes.map((fix) => (
              <li key={`${fix.title}-${fix.rationale}`} className="rounded-md border bg-muted/10 p-3">
                <p className="font-medium">
                  {fix.title}{' '}
                  <span className={`text-xs uppercase ${impactClass(fix.impact)}`}>
                    {fix.impact} impact
                  </span>
                </p>
                <p className="mt-1 text-muted-foreground">{fix.rationale}</p>
              </li>
            ))}
          </ol>
        </div>
      )}

      <p className="text-xs text-muted-foreground">{ats.methodology}</p>
    </div>
  )
}
