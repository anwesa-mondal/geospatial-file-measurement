export interface FileResponse {
  id: string
  filename: string
  file_size: number
  source_crs: string | null
  feature_count: number
  status: string
  error_message: string | null
  created_at: string
}

export interface MeasurementFeature {
  feature_index: number
  geometry_type: string | null
  properties: Record<string, any> | null
  validation_status: string
  validation_message: string | null
  area_sq_m: number | null
  perimeter_m: number | null
  length_m: number | null
  measurement_method: string | null
  measurement_crs: string | null
}

export interface PaginatedMeasurementsResponse {
  items: MeasurementFeature[]
  total: number
  page: number
  page_size: number
  pages: number
}
