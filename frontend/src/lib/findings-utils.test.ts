import { describe, expect, it } from 'vitest'

import { filterFindings, sortFindings } from '@/lib/findings-utils'
import type { RequirementFinding } from '@/types/api'

const sample: RequirementFinding[] = [
  {
    requirement_id: '1',
    label: 'Python',
    category: 'required_technical_skills',
    importance: 'required',
    status: 'matched',
    score_contribution: 1,
    evidence: [],
  },
  {
    requirement_id: '2',
    label: 'Kubernetes',
    category: 'tools_frameworks',
    importance: 'required',
    status: 'missing',
    score_contribution: 0,
    evidence: [],
  },
  {
    requirement_id: '3',
    label: 'React',
    category: 'preferred_skills',
    importance: 'preferred',
    status: 'partially_demonstrated',
    score_contribution: 0.55,
    evidence: [],
  },
]

describe('findings utils', () => {
  it('filters by category and status', () => {
    const filtered = filterFindings(sample, 'tools_frameworks', 'missing')
    expect(filtered).toHaveLength(1)
    expect(filtered[0].label).toBe('Kubernetes')
  })

  it('sorts by priority with missing required first', () => {
    const sorted = sortFindings(sample, 'priority')
    expect(sorted[0].label).toBe('Kubernetes')
  })
})
