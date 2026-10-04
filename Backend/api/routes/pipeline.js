import { Router } from 'express'

import { pool } from '../db.js'

const router = Router()

router.get('/', async (req, res) => {
  try {
    const runs = await pool.query(
      `SELECT run_id, started_at, finished_at, status, total_rows, summary, model_version
       FROM pipeline_runs
       ORDER BY started_at DESC
       LIMIT 10`,
    )

    if (runs.rows.length === 0) {
      return res.json({ latest_run: null, history: [] })
    }

    const latest = runs.rows[0]
    const stages = await pool.query(
      `SELECT stage_name AS name, status, started_at, finished_at,
              duration_ms, rows_in, rows_out, error_count, message
       FROM stage_runs
       WHERE run_id = $1
       ORDER BY id`,
      [latest.run_id],
    )

    // summary already contains the stages, so drop that copy to avoid sending them twice
    const { stages: _duplicate, ...summary } = latest.summary ?? {}

    res.json({
      latest_run: { ...latest, summary, stages: stages.rows },
      history: runs.rows.map(({ summary: _s, ...run }) => run),
    })
  } catch (err) {
    console.error(err)
    res.status(500).json({ error: 'Could not load pipeline status' })
  }
})

export default router