import { Router } from 'express'

import { pool } from '../db.js'

const router = Router()

const RANGES = { today: 1, '7d': 7, '30d': 30, '90d': 90 }

// Windows in India time. current = last N days including today, previous = the N days before that.
const WINDOWS = `
  WITH w AS (
    SELECT
      end_ts AS cur_end,
      end_ts - make_interval(days => $1::int) AS cur_start,
      end_ts - make_interval(days => $1::int * 2) AS prev_start
    FROM (
      SELECT (date_trunc('day', now() AT TIME ZONE 'Asia/Kolkata') + interval '1 day')
             AT TIME ZONE 'Asia/Kolkata' AS end_ts
    ) b
  )`

const KPI_SQL = `${WINDOWS}
  SELECT
    CASE WHEN t.timestamp >= w.cur_start THEN 'current' ELSE 'previous' END AS period,
    COUNT(*) AS total,
    COALESCE(SUM(t.amount), 0) AS volume,
    COUNT(*) FILTER (WHERE t.level IN ('HIGH', 'CRITICAL')) AS high_risk,
    COUNT(*) FILTER (WHERE t.decision = 'Approved') AS approved,
    COALESCE(AVG(t.risk_score), 0) AS avg_risk
  FROM transactions t, w
  WHERE t.timestamp >= w.prev_start AND t.timestamp < w.cur_end
  GROUP BY 1`

const DAILY_SQL = `${WINDOWS}
  SELECT
    to_char(t.timestamp AT TIME ZONE 'Asia/Kolkata', 'YYYY-MM-DD') AS date,
    COUNT(*) FILTER (WHERE t.decision = 'Approved') AS approved,
    COUNT(*) FILTER (WHERE t.decision = 'Review')   AS review,
    COUNT(*) FILTER (WHERE t.decision = 'Blocked')  AS blocked,
    COUNT(*) FILTER (WHERE t.level = 'LOW')         AS low,
    COUNT(*) FILTER (WHERE t.level = 'MEDIUM')      AS medium,
    COUNT(*) FILTER (WHERE t.level = 'HIGH')        AS high,
    COUNT(*) FILTER (WHERE t.level = 'CRITICAL')    AS critical
  FROM transactions t, w
  WHERE t.timestamp >= w.cur_start AND t.timestamp < w.cur_end
  GROUP BY 1
  ORDER BY 1`

const EMPTY_PERIOD = { total: 0, volume: 0, high_risk: 0, approved: 0, avg_risk: 0 }

const readPeriod = (rows, name) => {
  const row = rows.find((r) => r.period === name)
  if (!row) return EMPTY_PERIOD
  return {
    total: Number(row.total),
    volume: Number(row.volume),
    high_risk: Number(row.high_risk),
    approved: Number(row.approved),
    avg_risk: Number(row.avg_risk),
  }
}

const round = (n, digits = 1) => (n === null ? null : Number(n.toFixed(digits)))
const approvalRate = (p) => (p.total ? round((p.approved / p.total) * 100) : null)

// change_pct is null when there is nothing to compare against (avoids dividing by zero)
const kpi = (value, previous) => ({
  value,
  previous,
  change_pct: value !== null && previous ? round(((value - previous) / previous) * 100) : null,
})

router.get('/', async (req, res) => {
  const range = req.query.range ?? '30d'
  if (!Object.hasOwn(RANGES, range)) {
    return res.status(400).json({ error: `range must be one of: ${Object.keys(RANGES).join(', ')}` })
  }
  const days = RANGES[range]

  try {
    const [kpiRes, dailyRes, alertRes] = await Promise.all([
      pool.query(KPI_SQL, [days]),
      pool.query(DAILY_SQL, [days]),
      pool.query(`SELECT COUNT(*) AS count FROM transactions WHERE alert_status IN ('open', 'investigating')`),
    ])

    const cur = readPeriod(kpiRes.rows, 'current')
    const prev = readPeriod(kpiRes.rows, 'previous')

    const daily = dailyRes.rows.map((r) => ({
      date: r.date,
      approved: Number(r.approved),
      review: Number(r.review),
      blocked: Number(r.blocked),
      low: Number(r.low),
      medium: Number(r.medium),
      high: Number(r.high),
      critical: Number(r.critical),
    }))

    res.json({
      range,
      kpis: {
        total_transactions: kpi(cur.total, prev.total),
        total_volume: kpi(cur.volume, prev.volume),
        high_risk_count: kpi(cur.high_risk, prev.high_risk),
        approval_rate: kpi(approvalRate(cur), approvalRate(prev)),
        avg_risk_score: kpi(round(cur.avg_risk), round(prev.avg_risk)),
        active_alerts: { value: Number(alertRes.rows[0].count) },
      },
      daily_activity: daily.map(({ date, approved, review, blocked }) => ({ date, approved, review, blocked })),
      daily_risk: daily.map(({ date, low, medium, high, critical }) => ({ date, low, medium, high, critical })),
      risk_distribution: daily.reduce(
        (sum, d) => ({
          low: sum.low + d.low,
          medium: sum.medium + d.medium,
          high: sum.high + d.high,
          critical: sum.critical + d.critical,
        }),
        { low: 0, medium: 0, high: 0, critical: 0 },
      ),
    })
  } catch (err) {
    console.error(err)
    res.status(500).json({ error: 'Could not load overview' })
  }
})

export default router