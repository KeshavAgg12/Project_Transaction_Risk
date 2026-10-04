import express from 'express'

import healthRoutes from './routes/health.js'
import transactionRoutes from './routes/transactions.js'
import alertsRoutes from './routes/alerts.js'
import overviewRoutes from './routes/overview.js'
import pipelineRoutes from './routes/pipeline.js'
import riskAnalysisRoutes from './routes/riskAnalysis.js'
const app = express()
app.use(express.json())

app.use('/api/health', healthRoutes)
app.use('/api/transactions', transactionRoutes)
app.use('/api/pipeline', pipelineRoutes)
app.use('/api/overview', overviewRoutes)
app.use('/api/risk-analysis', riskAnalysisRoutes)
app.use('/api/alerts', alertsRoutes)

const PORT = 8000
app.listen(PORT, () => console.log(`API running on http://localhost:${PORT}`))