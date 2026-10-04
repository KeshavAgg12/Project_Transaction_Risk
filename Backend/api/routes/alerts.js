import { Router } from 'express'

import { pool } from '../db.js'

const router = Router()

const STATUSES = ['open', 'investigating', 'resolved']
const LEVELS = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

// Returns a number, the fallback when missing, or NaN when the value is not a whole number
const toInt = (value, fallback) => {
  if (value === undefined) return fallback
  const n = Number(value)
  return Number.isInteger(n) ? n : NaN
}

router.get('/', async (req, res) => {
  const { status, level, search } = req.query
  const page = toInt(req.query.page, 1)
  const pageSize = toInt(req.query.page_size, 10)

  if (!(page >= 1) || !(pageSize >= 1 && pageSize <= 100)) {
    return res.status(400).json({ error: 'page must be 1 or more and page_size between 1 and 100' })
  }
  if (status && !STATUSES.includes(status)) {
    return res.status(400).json({ error: `status must be one of: ${STATUSES.join(', ')}` })
  }
  if (level && !LEVELS.includes(level)) {
    return res.status(400).json({ error: `level must be one of: ${LEVELS.join(', ')}` })
  }

  // Build WHERE with $1, $2... placeholders so user input never goes into the SQL text
  const where = ['alert_status IS NOT NULL']
  const params = []
  if (status) {
    params.push(status)
    where.push(`alert_status = $${params.length}`)
  }
  if (level) {
    params.push(level)
    where.push(`level = $${params.length}`)
  }
  if (search) {
    params.push(`%${search}%`)
    where.push(`(transaction_id ILIKE $${params.length} OR customer_id ILIKE $${params.length})`)
  }
  const whereSql = `WHERE ${where.join(' AND ')}`

  try {
    const [listRes, totalRes, countsRes] = await Promise.all([
      pool.query(
        `SELECT transaction_id, timestamp, customer_id, amount, merchant_category,
                risk_score, level, decision, reasons, alert_status
         FROM transactions
         ${whereSql}
         ORDER BY timestamp DESC, transaction_id
         LIMIT $${params.length + 1} OFFSET $${params.length + 2}`,
        [...params, pageSize, (page - 1) * pageSize],
      ),
      pool.query(`SELECT COUNT(*) AS count FROM transactions ${whereSql}`, params),
      pool.query(
        `SELECT alert_status, COUNT(*) AS count
         FROM transactions
         WHERE alert_status IS NOT NULL
         GROUP BY alert_status`,
      ),
    ])

    const total = Number(totalRes.rows[0].count)

    const counts = { open: 0, investigating: 0, resolved: 0 }
    for (const row of countsRes.rows) counts[row.alert_status] = Number(row.count)

    res.json({
      items: listRes.rows.map((r) => ({ ...r, amount: Number(r.amount) })),
      page,
      page_size: pageSize,
      total,
      total_pages: Math.ceil(total / pageSize),
      counts: { ...counts, total: counts.open + counts.investigating + counts.resolved },
    })
  } catch (err) {
    console.error(err)
    res.status(500).json({ error: 'Could not load alerts' })
  }
})

export default router