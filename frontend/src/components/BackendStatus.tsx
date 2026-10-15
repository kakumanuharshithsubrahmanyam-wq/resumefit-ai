import { useCallback, useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { ApiClientError, fetchHealth, getApiBaseUrl } from '@/lib/api'
import type { HealthData } from '@/types/api'

type StatusState =
  | { kind: 'loading' }
  | { kind: 'connected'; data: HealthData }
  | { kind: 'error'; message: string; code?: string }

export function BackendStatus() {
  const [status, setStatus] = useState<StatusState>({ kind: 'loading' })

  const checkBackend = useCallback(async () => {
    setStatus({ kind: 'loading' })
    try {
      const response = await fetchHealth()
      setStatus({ kind: 'connected', data: response.data })
    } catch (error) {
      const message =
        error instanceof ApiClientError
          ? error.message
          : error instanceof Error
            ? error.message
            : 'Unable to reach the API'
      const code = error instanceof ApiClientError ? error.code : undefined
      setStatus({ kind: 'error', message, code })
    }
  }, [])

  useEffect(() => {
    void checkBackend()
  }, [checkBackend])

  return (
    <Card>
      <CardHeader>
        <CardTitle>API connectivity</CardTitle>
        <CardDescription>
          Backend base URL: <code className="text-xs">{getApiBaseUrl()}</code>
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {status.kind === 'loading' && (
          <p className="text-sm text-muted-foreground">Checking backend…</p>
        )}
        {status.kind === 'connected' && (
          <dl className="grid gap-2 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Status</dt>
              <dd className="font-medium text-emerald-700 dark:text-emerald-400">
                {status.data.status}
              </dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Service</dt>
              <dd>{status.data.service}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Timestamp</dt>
              <dd className="text-right font-mono text-xs">
                {status.data.timestamp}
              </dd>
            </div>
          </dl>
        )}
        {status.kind === 'error' && (
          <p className="text-sm text-destructive" role="alert">
            {status.code ? `[${status.code}] ` : ''}
            {status.message}
          </p>
        )}
        <Button type="button" variant="outline" onClick={() => void checkBackend()}>
          Retry connection
        </Button>
      </CardContent>
    </Card>
  )
}
