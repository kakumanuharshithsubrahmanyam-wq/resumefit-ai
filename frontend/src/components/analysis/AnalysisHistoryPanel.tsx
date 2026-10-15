import { Trash2 } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  ApiClientError,
  clearHistory,
  deleteHistoryItem,
  exportSavedAnalysisPdf,
  fetchHistory,
  fetchHistoryItem,
} from '@/lib/api'
import type { AnalysisHistoryItem, AnalysisResult } from '@/types/api'

type AnalysisHistoryPanelProps = {
  onOpen: (analysis: AnalysisResult) => void
  refreshToken?: number
}

export function AnalysisHistoryPanel({ onOpen, refreshToken = 0 }: AnalysisHistoryPanelProps) {
  const [items, setItems] = useState<AnalysisHistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetchHistory()
      setItems(response.data)
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Unable to load history.',
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load, refreshToken])

  async function handleDelete(id: string) {
    await deleteHistoryItem(id)
    await load()
  }

  async function handleClear() {
    await clearHistory()
    await load()
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Saved analyses (this browser)</CardTitle>
        <CardDescription>
          History is tied to a private browser session ID—not a user account. Clearing browser
          storage or switching devices will hide previous entries. Raw resume files are not
          stored.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {loading && (
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        )}
        {error && (
          <Alert variant="destructive">
            <AlertTitle>History unavailable</AlertTitle>
            <AlertDescription className="space-y-2">
              <p>{error}</p>
              <Button type="button" size="sm" variant="outline" onClick={() => void load()}>
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        )}
        {!loading && !error && items.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No saved analyses yet. Enable “Save this analysis to history” when running a report.
          </p>
        )}
        {!loading &&
          items.map((item) => (
            <div
              key={item.id}
              className="flex flex-col gap-2 rounded-md border p-3 sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <p className="text-sm font-medium">{item.job_title}</p>
                <p className="text-xs text-muted-foreground">
                  {new Date(item.created_at).toLocaleString()} ·{' '}
                  {item.overall_alignment.toFixed(1)}% alignment
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={async () => {
                    const record = await fetchHistoryItem(item.id)
                    onOpen(record.data.data)
                  }}
                >
                  Open
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => void exportSavedAnalysisPdf(item.id)}
                >
                  PDF
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  aria-label="Delete analysis"
                  onClick={() => void handleDelete(item.id)}
                >
                  <Trash2 className="size-4" />
                </Button>
              </div>
            </div>
          ))}
        {items.length > 0 && (
          <Button type="button" variant="outline" size="sm" onClick={() => void handleClear()}>
            Clear all history
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
