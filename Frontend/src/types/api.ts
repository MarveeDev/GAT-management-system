export interface Pagination {
  page: number
  per_page: number
  total: number
  pages: number
}

export interface AsyncSection<T> {
  data: T | null
  loading: boolean
  error: string | null
}
