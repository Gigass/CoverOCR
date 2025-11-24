export interface RecognizedText {
  content: string
  font?: string
  formatted_typography?: string
  confidence: number
  font_confidence?: number
}

export interface FontSummary {
  font: string
  occurrences: number
  avg_confidence: number
}

export interface ResultResponse {
  request_id: string
  texts: RecognizedText[]
  fonts_summary: FontSummary[]
  elapsed_ms: number
}

export interface UploadResponse {
  request_id: string
}
