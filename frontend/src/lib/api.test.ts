import { afterEach, describe, expect, it, vi } from 'vitest'

import { fetchHealth, getApiBaseUrl } from '@/lib/api'

describe('getApiBaseUrl', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('uses VITE_API_BASE_URL when set', () => {
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:9000/')
    expect(getApiBaseUrl()).toBe('http://localhost:9000')
  })

  it('falls back to local backend default', () => {
    vi.stubEnv('VITE_API_BASE_URL', '')
    expect(getApiBaseUrl()).toBe('http://127.0.0.1:8000')
  })
})

describe('fetchHealth', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('parses a successful health envelope', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          success: true,
          data: {
            status: 'ok',
            service: 'ResumeFit AI',
            timestamp: '2026-01-01T00:00:00+00:00',
          },
        }),
      }),
    )

    const result = await fetchHealth()
    expect(result.success).toBe(true)
    expect(result.data.status).toBe('ok')
  })
})
