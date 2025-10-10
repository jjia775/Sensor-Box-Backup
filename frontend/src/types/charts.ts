export type Threshold = { label: string; kind: 'upper' | 'lower'; value: number }

export type MetricInfo = {
  metric: string
  unit: string
  thresholds: Threshold[]
}

export type MetricsResp = { metrics: MetricInfo[] }

export type TimeseriesResp = {
  title: string
  unit: string
  labels: string[]
  series: { name: string; data: number[] }[]
  thresholds: Threshold[]
}
