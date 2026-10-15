import { sessionHeaders, syncAnalysisSessionId } from '@/lib/session'
import type {
  AnalysisHistoryItem,
  AnalysisResult,
  APIErrorBody,
  APIResponse,
  HealthData,
  JobDetails,
  ResumeParseData,
  ResumeParseMeta,
  RunAnalysisPayload,
  StoredAnalysisRecord,
} from '@/types/api'

export function getApiBaseUrl(): string {
  const base = import.meta.env.VITE_API_BASE_URL
  if (typeof base === 'string' && base.length > 0) {
    return base.replace(/\/$/, '')
  }
  if (import.meta.env.PROD) {
    console.error(
      'VITE_API_BASE_URL is not set. Configure the backend URL before production deployment.',
    )
  }
  return 'http://127.0.0.1:8000'
}

export class ApiClientError extends Error {
  readonly code: string
  readonly status: number
  readonly details?: Record<string, unknown> | null

  constructor(
    message: string,
    options: {
      code: string
      status: number
      details?: Record<string, unknown> | null
    },
  ) {
    super(message)
    this.name = 'ApiClientError'
    this.code = options.code
    this.status = options.status
    this.details = options.details
  }
}

async function parseErrorResponse(response: Response): Promise<ApiClientError> {
  try {
    const body = (await response.json()) as APIErrorBody
    if (body?.error?.message) {
      return new ApiClientError(body.error.message, {
        code: body.error.code ?? 'unknown_error',
        status: response.status,
        details: body.error.details,
      })
    }
  } catch {
    // Fall through to generic error below.
  }

  return new ApiClientError(response.statusText || 'Request failed', {
    code: 'http_error',
    status: response.status,
  })
}

async function readJsonResponse<T>(response: Response): Promise<APIResponse<T>> {
  syncAnalysisSessionId(response.headers?.get('X-Analysis-Session-Id'))
  if (!response.ok) {
    throw await parseErrorResponse(response)
  }
  return (await response.json()) as APIResponse<T>
}

export async function fetchHealth(): Promise<APIResponse<HealthData>> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/health`)
  return readJsonResponse(response)
}

export type ParseResumePayload = JobDetails & {
  file: File
  onProgress?: (percent: number) => void
}

export type ParseResumeResult = APIResponse<ResumeParseData> & {
  meta: ResumeParseMeta
}

export function parseResumeUpload({
  file,
  jobTitle,
  companyName,
  jobDescription,
  onProgress,
}: ParseResumePayload): Promise<ParseResumeResult> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('job_title', jobTitle.trim())
  formData.append('job_description', jobDescription.trim())
  if (companyName.trim()) {
    formData.append('company_name', companyName.trim())
  }

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${getApiBaseUrl()}/api/v1/resumes/parse`)
    xhr.responseType = 'json'

    xhr.upload.addEventListener('progress', (event) => {
      if (!event.lengthComputable || !onProgress) return
      const percent = Math.min(100, Math.round((event.loaded / event.total) * 100))
      onProgress(percent)
    })

    xhr.addEventListener('load', () => {
      const status = xhr.status
      const body = xhr.response as APIResponse<ResumeParseData> | APIErrorBody | null

      if (status >= 200 && status < 300 && body && 'success' in body && body.success) {
        resolve(body as ParseResumeResult)
        return
      }

      if (body && 'error' in body && body.error?.message) {
        reject(
          new ApiClientError(body.error.message, {
            code: body.error.code ?? 'unknown_error',
            status,
            details: body.error.details,
          }),
        )
        return
      }

      reject(
        new ApiClientError(xhr.statusText || 'Upload failed', {
          code: 'http_error',
          status,
        }),
      )
    })

    xhr.addEventListener('error', () => {
      reject(
        new ApiClientError('Network error while uploading the resume.', {
          code: 'network_error',
          status: 0,
        }),
      )
    })

    xhr.addEventListener('abort', () => {
      reject(
        new ApiClientError('Upload was cancelled.', {
          code: 'upload_aborted',
          status: 0,
        }),
      )
    })

    xhr.send(formData)
  })
}

export async function runAnalysis(
  payload: RunAnalysisPayload,
): Promise<APIResponse<AnalysisResult>> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/analysis/run`, {
    method: 'POST',
    headers: sessionHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      resume_text: payload.resumeText,
      job_title: payload.jobTitle.trim(),
      company_name: payload.companyName.trim() || null,
      job_description: payload.jobDescription.trim(),
      request_ai_recommendations: payload.requestAiRecommendations,
      ai_consent: payload.aiConsent,
      save_to_history: payload.saveToHistory,
      resume_filename: payload.resumeFilename ?? null,
    }),
  })
  return readJsonResponse(response)
}

export async function fetchHistory(): Promise<APIResponse<AnalysisHistoryItem[]>> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/history`, {
    headers: sessionHeaders(),
  })
  return readJsonResponse(response)
}

export async function fetchHistoryItem(
  recordId: string,
): Promise<APIResponse<StoredAnalysisRecord>> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/history/${recordId}`, {
    headers: sessionHeaders(),
  })
  return readJsonResponse(response)
}

export async function deleteHistoryItem(recordId: string): Promise<void> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/history/${recordId}`, {
    method: 'DELETE',
    headers: sessionHeaders(),
  })
  await readJsonResponse(response)
}

export async function clearHistory(): Promise<number> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/history`, {
    method: 'DELETE',
    headers: sessionHeaders(),
  })
  const body = await readJsonResponse<{ deleted_count: number }>(response)
  return body.data.deleted_count
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

export async function exportAnalysisPdf(analysis: AnalysisResult): Promise<void> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/analysis/export/pdf`, {
    method: 'POST',
    headers: sessionHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(analysis),
  })
  if (!response.ok) {
    throw await parseErrorResponse(response)
  }
  const blob = await response.blob()
  downloadBlob(blob, 'resumefit-analysis-report.pdf')
}

export async function exportSavedAnalysisPdf(recordId: string): Promise<void> {
  const response = await fetch(
    `${getApiBaseUrl()}/api/v1/analysis/${recordId}/export/pdf`,
    { headers: sessionHeaders() },
  )
  if (!response.ok) {
    throw await parseErrorResponse(response)
  }
  const blob = await response.blob()
  downloadBlob(blob, `resumefit-analysis-${recordId}.pdf`)
}
