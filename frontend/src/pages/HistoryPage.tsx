import { useState } from 'react'
import { Link } from 'react-router-dom'

import { AnalysisHistoryPanel } from '@/components/analysis/AnalysisHistoryPanel'
import { ResultsDashboard } from '@/components/analysis/ResultsDashboard'
import { Button } from '@/components/ui/button'
import type { AnalysisResult, JobDetails } from '@/types/api'

const emptyJobDetails: JobDetails = {
  jobTitle: '',
  companyName: '',
  jobDescription: '',
}

export function HistoryPage() {
  const [opened, setOpened] = useState<AnalysisResult | null>(null)

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Analysis history</h1>
          <p className="mt-2 max-w-2xl text-muted-foreground">
            Reopen saved reports from this browser session. History is not shared across users
            or devices and does not include uploaded resume files.
          </p>
        </div>
        <Button asChild variant="outline">
          <Link to="/analyze">New analysis</Link>
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <AnalysisHistoryPanel
          onOpen={(analysis) => {
            setOpened(analysis)
          }}
        />
        <ResultsDashboard
          jobDetails={
            opened
              ? {
                  jobTitle: opened.job_title,
                  companyName: opened.company_name ?? '',
                  jobDescription: '',
                }
              : emptyJobDetails
          }
          parseResult={null}
          analysisResult={opened}
          loading={false}
        />
      </div>
    </main>
  )
}
