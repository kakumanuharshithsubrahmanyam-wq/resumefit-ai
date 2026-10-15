import { FileText, Upload, X } from 'lucide-react'
import { useCallback, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import {
  ACCEPTED_RESUME_EXTENSIONS,
  ACCEPTED_RESUME_TYPES,
  formatFileSize,
  getMaxUploadBytes,
} from '@/lib/constants'
import { cn } from '@/lib/utils'

type ResumeDropzoneProps = {
  file: File | null
  onFileChange: (file: File | null) => void
  uploadProgress: number | null
  disabled?: boolean
  error?: string | null
}

function isAcceptedFile(file: File): boolean {
  const lower = file.name.toLowerCase()
  const hasExtension = ACCEPTED_RESUME_EXTENSIONS.some((ext) =>
    lower.endsWith(ext),
  )
  const hasMime = ACCEPTED_RESUME_TYPES.includes(
    file.type as (typeof ACCEPTED_RESUME_TYPES)[number],
  )
  return hasExtension || hasMime
}

export function ResumeDropzone({
  file,
  onFileChange,
  uploadProgress,
  disabled = false,
  error,
}: ResumeDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragActive, setDragActive] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)
  const maxBytes = getMaxUploadBytes()

  const validateAndSet = useCallback(
    (next: File | null) => {
      setLocalError(null)
      if (!next) {
        onFileChange(null)
        return
      }
      if (!isAcceptedFile(next)) {
        setLocalError('Please upload a PDF or DOCX resume.')
        return
      }
      if (next.size > maxBytes) {
        setLocalError(
          `File is too large. Maximum size is ${formatFileSize(maxBytes)}.`,
        )
        return
      }
      onFileChange(next)
    },
    [maxBytes, onFileChange],
  )

  const onBrowse = () => inputRef.current?.click()

  const displayError = error ?? localError

  return (
    <div className="space-y-3">
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_RESUME_EXTENSIONS.join(',')}
        className="sr-only"
        disabled={disabled}
        onChange={(event) => {
          const next = event.target.files?.[0] ?? null
          validateAndSet(next)
          event.target.value = ''
        }}
      />

      {!file ? (
        <div
          onDragEnter={(event) => {
            event.preventDefault()
            if (!disabled) setDragActive(true)
          }}
          onDragOver={(event) => {
            event.preventDefault()
            if (!disabled) setDragActive(true)
          }}
          onDragLeave={(event) => {
            event.preventDefault()
            setDragActive(false)
          }}
          onDrop={(event) => {
            event.preventDefault()
            setDragActive(false)
            if (disabled) return
            const next = event.dataTransfer.files?.[0] ?? null
            validateAndSet(next)
          }}
          className={cn(
            'group relative flex min-h-44 flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-8 text-center transition-all duration-200',
            dragActive
              ? 'border-violet-500 bg-violet-50/70 dark:bg-violet-950/20'
              : 'border-border bg-card/70 hover:border-indigo-300 hover:bg-indigo-50/40 dark:hover:bg-indigo-950/10',
            disabled && 'pointer-events-none opacity-60',
          )}
        >
          <div className="mb-3 inline-flex size-12 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500/15 to-violet-500/15 text-indigo-600 transition-transform duration-200 group-hover:scale-105">
            <Upload className="size-5" aria-hidden="true" />
          </div>
          <p className="text-sm font-medium">Drag and drop your resume</p>
          <p className="mt-1 text-xs text-muted-foreground">
            PDF or DOCX · up to {formatFileSize(maxBytes)}
          </p>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="mt-4"
            onClick={onBrowse}
            disabled={disabled}
          >
            Browse files
          </Button>
        </div>
      ) : (
        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="inline-flex size-10 shrink-0 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-600">
              <FileText className="size-5" aria-hidden="true" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{file.name}</p>
              <p className="text-xs text-muted-foreground">
                {formatFileSize(file.size)}
              </p>
              {uploadProgress !== null && (
                <div className="mt-3 space-y-1">
                  <Progress value={uploadProgress} />
                  <p className="text-xs text-muted-foreground">
                    Uploading… {uploadProgress}%
                  </p>
                </div>
              )}
            </div>
            <div className="flex shrink-0 gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={onBrowse}
                disabled={disabled}
              >
                Replace
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => validateAndSet(null)}
                disabled={disabled}
                aria-label="Remove file"
              >
                <X className="size-4" />
              </Button>
            </div>
          </div>
        </div>
      )}

      {displayError && (
        <p className="text-sm text-destructive" role="alert">
          {displayError}
        </p>
      )}
    </div>
  )
}
