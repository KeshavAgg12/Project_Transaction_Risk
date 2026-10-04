// Synthetic demo data.
export const pipeline = [
  ['Transaction Ingestion', 'Healthy', 1.31e6, 12, 0.02], ['Validation', 'Healthy', 1.31e6, 9, 0.11], ['Normalization', 'Healthy', 1.3e6, 14, 0.04],
  ['Feature Engineering', 'Warning', 1.24e6, 38, 0.08], ['Risk Evaluation', 'Processing', 1.24e6, 52, 0.05], ['Rule Engine', 'Healthy', 1.23e6, 21, 0.03],
  ['Decision', 'Healthy', 1.23e6, 7, 0.01], ['Alert / Approval / Block', 'Healthy', 1.23e6, 11, 0.02],
].map(([name, status, processed, latency, errors]) => ({ name, status, processed, latency, errors }))
export const riskFactors = [
  ['Unusual transaction amount', 'High', 28, 'Triggered'], ['New device', 'Medium', 21, 'Triggered'], ['Geographic anomaly', 'High', 24, 'Triggered'],
  ['Velocity anomaly', 'Medium', 14, 'Triggered'], ['Suspicious merchant pattern', 'Low', 9, 'Watching'],
]
