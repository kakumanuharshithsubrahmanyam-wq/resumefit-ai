import { useState, type FormEvent } from 'react'

import { AnalysisHistoryPanel } from '@/components/analysis/AnalysisHistoryPanel'
import { JobDetailsForm } from '@/components/analysis/JobDetailsForm'
import { ResultsDashboard } from '@/components/analysis/ResultsDashboard'
import { ResumeDropzone } from '@/components/upload/ResumeDropzone'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { ApiClientError, parseResumeUpload, runAnalysis } from '@/lib/api'
import type { AnalysisResult, JobDetails, ResumeParseData } from '@/types/api'

const initialJobDetails: JobDetails = {
  jobTitle: '',
  companyName: '',
  jobDescription: '',
}

export function AnalyzePage() {
  const [jobDetails, setJobDetails] = useState<JobDetails>(initialJobDetails)
  const [file, setFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [parseResult, setParseResult] = useState<ResumeParseData | null>(null)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [requestAi, setRequestAi] = useState(false)
  const [aiConsent, setAiConsent] = useState(false)
  const [saveToHistory, setSaveToHistory] = useState(true)
  const [historyRefresh, setHistoryRefresh] = useState(0)
  const [lastResumeText, setLastResumeText] = useState<string | null>(null)

  const canSubmit =
    !!file &&
    jobDetails.jobTitle.trim().length > 0 &&
    jobDetails.jobDescription.trim().length > 0 &&
    !loading &&
    (!requestAi || aiConsent)

  async function runFullAnalysis(resumeText: string, filename: string) {
    const analysisResponse = await runAnalysis({
      resumeText,
      jobTitle: jobDetails.jobTitle,
      companyName: jobDetails.companyName,
      jobDescription: jobDetails.jobDescription,
      requestAiRecommendations: requestAi,
      aiConsent,
      saveToHistory,
      resumeFilename: filename,
    })
    setAnalysisResult(analysisResponse.data)
    if (saveToHistory) {
      setHistoryRefresh((value) => value + 1)
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!file || !canSubmit) return

    setError(null)
    setLoading(true)
    setUploadProgress(0)
    setAnalysisResult(null)

    try {
      const parseResponse = await parseResumeUpload({
        file,
        jobTitle: jobDetails.jobTitle,
        companyName: jobDetails.companyName,
        jobDescription: jobDetails.jobDescription,
        onProgress: setUploadProgress,
      })
      setParseResult(parseResponse.data)
      setLastResumeText(parseResponse.data.text)
      await runFullAnalysis(parseResponse.data.text, parseResponse.data.filename)
    } catch (err) {
      const message =
        err instanceof ApiClientError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Unable to complete analysis.'
      setError(message)
    } finally {
      setLoading(false)
      setUploadProgress(null)
    }
  }

  async function retryAnalysisOnly() {
    if (!lastResumeText || !parseResult) return
    setError(null)
    setLoading(true)
    try {
      await runFullAnalysis(lastResumeText, parseResult.filename)
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Unable to complete analysis.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
      <div className="mb-8 space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">Resume analysis</h1>
        <p className="max-w-3xl text-muted-foreground">
          Upload your resume, run deterministic alignment scoring, export a PDF report, and
          optionally save structured results to this browser&apos;s private session history.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <form onSubmit={(event) => void handleSubmit(event)} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Resume upload</CardTitle>
              <CardDescription>
                Drag and drop a PDF or DOCX file, or browse to select one.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResumeDropzone
                file={file}
                onFileChange={setFile}
                uploadProgress={uploadProgress}
                disabled={loading}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Target role</CardTitle>
              <CardDescription>
                Job details are preserved if upload, parsing, or analysis fails.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <JobDetailsForm
                value={jobDetails}
                onChange={setJobDetails}
                disabled={loading}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>AI recommendations (optional)</CardTitle>
              <CardDescription>
                Resume and job text are sent to an external provider only when enabled and
                consented.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <label className="flex items-start gap-3 text-sm">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={requestAi}
                  disabled={loading}
                  onChange={(event) => setRequestAi(event.target.checked)}
                />
                <span>Request AI-generated learning and resume suggestions</span>
              </label>
              {requestAi && (
                <div className="space-y-2 rounded-md border border-indigo-200 bg-indigo-50/60 p-3 dark:border-indigo-900 dark:bg-indigo-950/20">
                  <Label htmlFor="ai-consent" className="font-normal">
                    Consent to external AI processing
                  </Label>
                  <label htmlFor="ai-consent" className="flex items-start gap-3 text-sm">
                    <input
                      id="ai-consent"
                      type="checkbox"
                      className="mt-1"
                      checked={aiConsent}
                      disabled={loading}
                      onChange={(event) => setAiConsent(event.target.checked)}
                    />
                    <span>
                      I consent to sending my resume and job description text to the configured
                      AI provider for recommendation generation.
                    </span>
                  </label>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>History & retention</CardTitle>
              <CardDescription>
                Saved analyses store structured scores and findings—not raw resume files.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <label className="flex items-start gap-3 text-sm">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={saveToHistory}
                  disabled={loading}
                  onChange={(event) => setSaveToHistory(event.target.checked)}
                />
                <span>Save this analysis to browser session history</span>
              </label>
            </CardContent>
          </Card>

          {error && !analysisResult && (
            <Alert variant="destructive">
              <AlertTitle>Analysis failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Button type="submit" size="lg" disabled={!canSubmit} className="w-full sm:w-auto">
            {loading ? 'Analyzing…' : 'Analyze resume fit'}
          </Button>
        </form>

        <div className="space-y-6">
          <ResultsDashboard
            jobDetails={jobDetails}
            parseResult={parseResult}
            analysisResult={analysisResult}
            loading={loading}
            error={analysisResult ? null : error}
            onRetry={
              parseResult && lastResumeText ? () => void retryAnalysisOnly() : undefined
            }
          />
          <AnalysisHistoryPanel
            refreshToken={historyRefresh}
            onOpen={(analysis) => {
              setAnalysisResult(analysis)
              setJobDetails({
                jobTitle: analysis.job_title,
                companyName: analysis.company_name ?? '',
                jobDescription: jobDetails.jobDescription,
              })
              setError(null)
            }}
          />
        </div>
      </div>
    </main>
  )
}
