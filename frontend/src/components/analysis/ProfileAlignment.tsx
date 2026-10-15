import type { ResumeProfile } from '@/types/api'

type ProfileAlignmentProps = {
  profile: ResumeProfile
}

function Section({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null
  return (
    <div className="rounded-lg border bg-muted/10 p-3">
      <p className="text-sm font-medium">{title}</p>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

export function ProfileAlignment({ profile }: ProfileAlignmentProps) {
  const hasContent =
    profile.explicit_skills.length > 0 ||
    profile.demonstrated_skills.length > 0 ||
    profile.responsibilities.length > 0 ||
    profile.achievements.length > 0 ||
    profile.education.length > 0 ||
    profile.certifications.length > 0

  if (!hasContent) {
    return (
      <p className="text-sm text-muted-foreground">
        No structured experience, project, or education sections were detected in the parsed
        resume text.
      </p>
    )
  }

  return (
    <div className="space-y-3">
      {(profile.explicit_skills.length > 0 || profile.demonstrated_skills.length > 0) && (
        <div className="rounded-lg border bg-muted/10 p-3 text-sm">
          <p className="font-medium">Skills evidence</p>
          {profile.explicit_skills.length > 0 && (
            <p className="mt-1 text-muted-foreground">
              Explicit: {profile.explicit_skills.join(', ')}
            </p>
          )}
          {profile.demonstrated_skills.length > 0 && (
            <p className="mt-1 text-muted-foreground">
              Demonstrated: {profile.demonstrated_skills.join(', ')}
            </p>
          )}
        </div>
      )}
      <Section title="Experience & responsibilities" items={profile.responsibilities} />
      <Section title="Achievements" items={profile.achievements} />
      <Section title="Education" items={profile.education} />
      <Section title="Certifications" items={profile.certifications} />
    </div>
  )
}
