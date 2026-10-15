const SESSION_KEY = 'resumefit_analysis_session_id'

export function getAnalysisSessionId(): string {
  if (typeof window === 'undefined') {
    return 'server'
  }
  const existing = window.sessionStorage.getItem(SESSION_KEY)
  if (existing) {
    return existing
  }
  const created = crypto.randomUUID()
  window.sessionStorage.setItem(SESSION_KEY, created)
  return created
}

export function syncAnalysisSessionId(headerValue: string | null | undefined): void {
  if (!headerValue || typeof window === 'undefined') return
  window.sessionStorage.setItem(SESSION_KEY, headerValue)
}

export function sessionHeaders(extra?: HeadersInit): HeadersInit {
  return {
    ...extra,
    'X-Analysis-Session-Id': getAnalysisSessionId(),
  }
}
