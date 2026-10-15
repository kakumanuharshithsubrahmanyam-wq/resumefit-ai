import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import type { JobDetails } from '@/types/api'

type JobDetailsFormProps = {
  value: JobDetails
  onChange: (next: JobDetails) => void
  disabled?: boolean
}

export function JobDetailsForm({
  value,
  onChange,
  disabled = false,
}: JobDetailsFormProps) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="job-title">Job title</Label>
        <Input
          id="job-title"
          placeholder="Senior Backend Engineer"
          value={value.jobTitle}
          disabled={disabled}
          onChange={(event) =>
            onChange({ ...value, jobTitle: event.target.value })
          }
          required
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="company-name">Company (optional)</Label>
        <Input
          id="company-name"
          placeholder="Acme Corp"
          value={value.companyName}
          disabled={disabled}
          onChange={(event) =>
            onChange({ ...value, companyName: event.target.value })
          }
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="job-description">Job description</Label>
        <Textarea
          id="job-description"
          placeholder="Paste the role requirements, responsibilities, and preferred qualifications…"
          value={value.jobDescription}
          disabled={disabled}
          onChange={(event) =>
            onChange({ ...value, jobDescription: event.target.value })
          }
          required
          className="min-h-40"
        />
        <p className="text-xs text-muted-foreground">
          {value.jobDescription.trim().length.toLocaleString()} characters
        </p>
      </div>
    </div>
  )
}
