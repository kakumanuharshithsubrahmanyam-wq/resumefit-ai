import { BarChart3, ClipboardList, Download, Sparkles, Target, UserRoundSearch } from 'lucide-react'
import { useState } from 'react'

import { FindingsPanel } from '@/components/analysis/FindingsPanel'
import { ProfileAlignment } from '@/components/analysis/ProfileAlignment'
import { RecommendationsPanel } from '@/components/analysis/RecommendationsPanel'
import { AtsCompatibilityPanel } from '@/components/analysis/AtsCompatibilityPanel'
import { ScoreOverview } from '@/components/analysis/ScoreOverview'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { exportAnalysisPdf, exportSavedAnalysisPdf } from '@/lib/api'
import { formatFileSize } from '@/lib/constants'
import type { AnalysisResult, JobDetails, ResumeParseData } from '@/types/api'

type ResultsDashboardProps = {
  jobDetails: JobDetails
  parseResult: ResumeParseData | null
  analysisResult: AnalysisResult | null
  loading: boolean
  error?: string | null
  onRetry?: () => void
}

export function ResultsDashboard({
  jobDetails,
  parseResult,
  analysisResult,
  loading,
  error,
  onRetry,
}: ResultsDashboardProps) {
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  async function handleExport() {
    if (!analysisResult) return
    setExportError(null)
    setExporting(true)
    try {
      if (analysisResult.record_id) {
        await exportSavedAnalysisPdf(analysisResult.record_id)
      } else {
        await exportAnalysisPdf(analysisResult)
      }
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'Unable to export PDF.')
    } finally {
      setExporting(false)
    }
  }

  if (loading) {
    return (
      <Card className="animate-in fade-in duration-300">
        <CardHeader>
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-4 w-full max-w-sm" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Results unavailable</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Alert variant="destructive">
            <AlertTitle>Analysis error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          {onRetry && (
            <Button type="button" variant="outline" onClick={onRetry}>
              Retry analysis
            </Button>
          )}
        </CardContent>
      </Card>
    )
  }

  if (!parseResult && !analysisResult) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Results dashboard</CardTitle>
          <CardDescription>
            Upload a resume and run analysis to see scores, evidence-backed findings, and
            recommendations.
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  const scoring = analysisResult?.analysis.scoring

  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center gap-2">
            <CardTitle>Results dashboard</CardTitle>
            {parseResult && <Badge>Parsed</Badge>}
            {analysisResult && <Badge variant="secondary">Analyzed</Badge>}
          </div>
          <CardDescription>
            Alignment review for{' '}
            <span className="font-medium text-foreground">
              {jobDetails.jobTitle.trim() || analysisResult?.job_title || 'target role'}
            </span>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {parseResult && (
            <Alert variant="success">
              <Sparkles className="size-4" aria-hidden="true" />
              <AlertTitle>Resume parsed</AlertTitle>
              <AlertDescription>
                {parseResult.filename} · {parseResult.format.toUpperCase()} ·{' '}
                {formatFileSize(parseResult.size_bytes)} ·{' '}
                {parseResult.word_count.toLocaleString()} words
              </AlertDescription>
            </Alert>
          )}
          {analysisResult && (
            <Button
              type="button"
              variant="outline"
              disabled={exporting}
              onClick={() => void handleExport()}
            >
              <Download className="size-4" aria-hidden="true" />
              {exporting ? 'Generating PDF…' : 'Download PDF report'}
            </Button>
          )}
          {exportError && (
            <p className="text-sm text-destructive" role="alert">
              {exportError}
            </p>
          )}
        </CardContent>
      </Card>

      {scoring && analysisResult && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Target className="size-4" />
                Job Match & ATS scores
              </CardTitle>
              <CardDescription>
                Job Match measures evidence alignment; Estimated ATS Compatibility reflects
                parse-friendly structure and keyword communication in extracted text.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <ScoreOverview scoring={scoring} />
              <AtsCompatibilityPanel ats={analysisResult.analysis.ats_compatibility} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <BarChart3 className="size-4" />
                Requirement findings
              </CardTitle>
              <CardDescription>
                Filter, sort, and expand items to inspect evidence for matches and gaps.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FindingsPanel findings={analysisResult.analysis.findings} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <UserRoundSearch className="size-4" />
                Experience & education alignment
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ProfileAlignment profile={analysisResult.analysis.resume_profile} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <ClipboardList className="size-4" />
                Recommendations & learning plan
              </CardTitle>
            </CardHeader>
            <CardContent>
              <RecommendationsPanel recommendations={analysisResult.recommendations} />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
