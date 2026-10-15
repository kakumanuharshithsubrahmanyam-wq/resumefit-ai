import type { MatchStatus, RequirementCategory, RequirementFinding } from '@/types/api'

export type SortOption = 'priority' | 'status' | 'label'

const STATUS_ORDER: Record<MatchStatus, number> = {
  missing: 0,
  uncertain: 1,
  partially_demonstrated: 2,
  matched: 3,
}

const IMPORTANCE_ORDER = {
  required: 0,
  preferred: 1,
  nice_to_have: 2,
} as const

export function filterFindings(
  findings: RequirementFinding[],
  category: RequirementCategory | 'all',
  status: MatchStatus | 'all',
): RequirementFinding[] {
  return findings.filter((finding) => {
    const categoryMatch = category === 'all' || finding.category === category
    const statusMatch = status === 'all' || finding.status === status
    return categoryMatch && statusMatch
  })
}

export function sortFindings(
  findings: RequirementFinding[],
  sortBy: SortOption,
): RequirementFinding[] {
  const copy = [...findings]
  if (sortBy === 'label') {
    return copy.sort((a, b) => a.label.localeCompare(b.label))
  }
  if (sortBy === 'status') {
    return copy.sort((a, b) => STATUS_ORDER[a.status] - STATUS_ORDER[b.status])
  }
  return copy.sort((a, b) => {
    const importanceDiff =
      IMPORTANCE_ORDER[a.importance] - IMPORTANCE_ORDER[b.importance]
    if (importanceDiff !== 0) return importanceDiff
    return STATUS_ORDER[a.status] - STATUS_ORDER[b.status]
  })
}

export function categoryLabel(category: RequirementCategory): string {
  const labels: Record<RequirementCategory, string> = {
    required_technical_skills: 'Required technical',
    preferred_skills: 'Preferred skills',
    tools_frameworks: 'Tools & frameworks',
    experience_responsibilities: 'Experience',
    education_certifications: 'Education & certs',
    domain_soft_skills: 'Domain & soft skills',
  }
  return labels[category]
}
