import { ChevronDown } from 'lucide-react'
import { useMemo, useState } from 'react'

import { categoryLabel, filterFindings, sortFindings, type SortOption } from '@/lib/findings-utils'
import { cn } from '@/lib/utils'
import type { MatchStatus, RequirementCategory, RequirementFinding } from '@/types/api'

const STATUS_LABEL: Record<MatchStatus, string> = {
  matched: 'Matched',
  partially_demonstrated: 'Partial',
  missing: 'Missing',
  uncertain: 'Uncertain',
}

const STATUS_CLASS: Record<MatchStatus, string> = {
  matched: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200',
  partially_demonstrated: 'bg-amber-100 text-amber-900 dark:bg-amber-950/40 dark:text-amber-100',
  missing: 'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-200',
  uncertain: 'bg-slate-100 text-slate-700 dark:bg-slate-900 dark:text-slate-200',
}

type FindingsPanelProps = {
  findings: RequirementFinding[]
}

export function FindingsPanel({ findings }: FindingsPanelProps) {
  const [category, setCategory] = useState<RequirementCategory | 'all'>('all')
  const [status, setStatus] = useState<MatchStatus | 'all'>('all')
  const [sortBy, setSortBy] = useState<SortOption>('priority')
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  const visible = useMemo(
    () => sortFindings(filterFindings(findings, category, status), sortBy),
    [findings, category, status, sortBy],
  )

  return (
    <div className="space-y-4">
      <div className="grid gap-2 sm:grid-cols-3">
        <label className="text-xs">
          Category
          <select
            className="mt-1 w-full rounded-md border bg-background px-2 py-1.5 text-sm"
            value={category}
            onChange={(event) =>
              setCategory(event.target.value as RequirementCategory | 'all')
            }
          >
            <option value="all">All categories</option>
            <option value="required_technical_skills">Required technical</option>
            <option value="preferred_skills">Preferred skills</option>
            <option value="tools_frameworks">Tools & frameworks</option>
            <option value="experience_responsibilities">Experience</option>
            <option value="education_certifications">Education & certs</option>
            <option value="domain_soft_skills">Domain & soft skills</option>
          </select>
        </label>
        <label className="text-xs">
          Status
          <select
            className="mt-1 w-full rounded-md border bg-background px-2 py-1.5 text-sm"
            value={status}
            onChange={(event) => setStatus(event.target.value as MatchStatus | 'all')}
          >
            <option value="all">All statuses</option>
            <option value="matched">Matched</option>
            <option value="partially_demonstrated">Partial</option>
            <option value="missing">Missing</option>
            <option value="uncertain">Uncertain</option>
          </select>
        </label>
        <label className="text-xs">
          Sort
          <select
            className="mt-1 w-full rounded-md border bg-background px-2 py-1.5 text-sm"
            value={sortBy}
            onChange={(event) => setSortBy(event.target.value as SortOption)}
          >
            <option value="priority">Priority</option>
            <option value="status">Status</option>
            <option value="label">Label</option>
          </select>
        </label>
      </div>

      {visible.length === 0 ? (
        <p className="text-sm text-muted-foreground">No findings match the current filters.</p>
      ) : (
        <div className="space-y-2">
          {visible.map((finding) => {
            const isOpen = expanded[finding.requirement_id] ?? false
            return (
              <div key={finding.requirement_id} className="rounded-lg border p-3">
                <button
                  type="button"
                  className="flex w-full items-start justify-between gap-3 text-left"
                  onClick={() =>
                    setExpanded((prev) => ({
                      ...prev,
                      [finding.requirement_id]: !isOpen,
                    }))
                  }
                >
                  <div>
                    <p className="font-medium">{finding.label}</p>
                    <p className="text-xs text-muted-foreground">
                      {categoryLabel(finding.category)} · {finding.importance}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        'rounded-full px-2 py-0.5 text-xs font-medium',
                        STATUS_CLASS[finding.status],
                      )}
                    >
                      {STATUS_LABEL[finding.status]}
                    </span>
                    <ChevronDown
                      className={cn('size-4 transition-transform', isOpen && 'rotate-180')}
                    />
                  </div>
                </button>
                {isOpen && (
                  <div className="mt-3 space-y-2 border-t pt-3 text-sm">
                    {finding.notes && (
                      <p className="text-muted-foreground">{finding.notes}</p>
                    )}
                    {finding.evidence.length > 0 ? (
                      <ul className="space-y-1 text-muted-foreground">
                        {finding.evidence.map((item) => (
                          <li key={item} className="whitespace-pre-wrap">
                            “{item}”
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-muted-foreground">No evidence snippets available.</p>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
