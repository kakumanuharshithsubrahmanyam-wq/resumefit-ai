import type { AnalysisResult } from '@/types/api'

type RecommendationsPanelProps = {
  recommendations: AnalysisResult['recommendations']
}

export function RecommendationsPanel({ recommendations }: RecommendationsPanelProps) {
  if (!recommendations.enabled && recommendations.provider === 'disabled') {
    return (
      <p className="text-sm text-muted-foreground">
        AI recommendations were not requested for this analysis. Deterministic findings and
        scores are still available above.
      </p>
    )
  }

  return (
    <div className="space-y-4 text-sm">
      <p className="text-muted-foreground">
        Provider: {recommendations.provider}. These suggestions supplement—but never
        override—the deterministic scores and classifications.
      </p>
      {recommendations.notes && <p className="text-muted-foreground">{recommendations.notes}</p>}

      {recommendations.gap_explanations.length > 0 && (
        <div>
          <p className="mb-2 font-medium">Prioritized gap explanations</p>
          <ul className="list-disc space-y-1 pl-5 text-muted-foreground">
            {recommendations.gap_explanations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {recommendations.skill_improvements.length > 0 && (
        <div className="space-y-2">
          <p className="font-medium">Skill improvement recommendations</p>
          {recommendations.skill_improvements.map((item) => (
            <div key={item.title} className="rounded-md border p-3">
              <p className="font-medium">{item.title}</p>
              <p className="mt-1 text-muted-foreground">{item.rationale}</p>
              <p className="mt-1 text-xs uppercase tracking-wide text-muted-foreground">
                Grounded in: {item.grounded_in.replace('_', ' ')}
              </p>
            </div>
          ))}
        </div>
      )}

      {recommendations.learning_topics.length > 0 && (
        <div>
          <p className="mb-2 font-medium">Learning topics</p>
          <ul className="flex flex-wrap gap-2">
            {recommendations.learning_topics.map((topic) => (
              <li
                key={topic}
                className="rounded-full border bg-indigo-50 px-2.5 py-1 text-xs dark:bg-indigo-950/30"
              >
                {topic}
              </li>
            ))}
          </ul>
        </div>
      )}

      {recommendations.project_ideas.length > 0 && (
        <div>
          <p className="mb-2 font-medium">Practical project ideas</p>
          <ul className="list-disc space-y-1 pl-5 text-muted-foreground">
            {recommendations.project_ideas.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {recommendations.learning_plan.length > 0 && (
        <div className="space-y-2">
          <p className="font-medium">Learning plan</p>
          {recommendations.learning_plan.map((step) => (
            <div key={step.title} className="rounded-md border p-3">
              <p className="font-medium">{step.title}</p>
              <p className="text-xs text-muted-foreground">
                {step.focus} · {step.estimated_effort}
              </p>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">
                {step.actions.map((action) => (
                  <li key={action}>{action}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      {recommendations.resume_bullet_suggestions.length > 0 && (
        <div>
          <p className="mb-2 font-medium">Resume bullet suggestions</p>
          <ul className="space-y-2 text-muted-foreground">
            {recommendations.resume_bullet_suggestions.map((bullet) => (
              <li key={bullet} className="rounded-md bg-muted/30 p-2">
                {bullet}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
