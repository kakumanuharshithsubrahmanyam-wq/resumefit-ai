const DEFAULT_MAX_UPLOAD_BYTES = 5 * 1024 * 1024

export function getMaxUploadBytes(): number {
  const raw = import.meta.env.VITE_MAX_UPLOAD_BYTES
  if (typeof raw === 'string' && raw.trim().length > 0) {
    const parsed = Number.parseInt(raw, 10)
    if (Number.isFinite(parsed) && parsed > 0) {
      return parsed
    }
  }
  return DEFAULT_MAX_UPLOAD_BYTES
}

export const ACCEPTED_RESUME_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
] as const

export const ACCEPTED_RESUME_EXTENSIONS = ['.pdf', '.docx'] as const

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}
