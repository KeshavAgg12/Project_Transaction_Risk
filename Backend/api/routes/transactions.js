import { pool } from '../db.js';
import { Router } from 'express';

const router = Router();

const SORT_COLUMNS = {
  time: 'timestamp',
  risk: 'risk_score',
  amount: 'amount',
};

const FILTERS = ['level', 'decision', 'source', 'payment_method', 'merchant_category'];
// sort, filter, pagination
router.get('/', async (req, res) => {
  try {
    // pagination
    const page_size = Math.min(Math.max(Math.floor(Number(req.query.page_size)) || 10, 1), 100);
    const page = Math.max(Math.floor(Number(req.query.page)) || 1, 1);
    const offset = (page - 1) * page_size;

    // sort (sirf map ki value query mein jati hai)
    const sortKey = Object.hasOwn(SORT_COLUMNS, req.query.sort) ? req.query.sort : 'time';
    const sortColumn = SORT_COLUMNS[sortKey];
    const sortOrder = req.query.order === 'asc' ? 'ASC' : 'DESC';

    // dynamic WHERE
    const conditions = [];
    const params = [];

    for (const key of FILTERS) {
      const value = req.query[key];
      if (typeof value === 'string' && value) {
        params.push(value);
        conditions.push(`${key} = $${params.length}`);
      }
    }

    const search = req.query.search;
    if (typeof search === 'string' && search.trim()) {
      params.push(`%${search.trim()}%`);
      const n = params.length;
      conditions.push(`(transaction_id ILIKE $${n} OR customer_id ILIKE $${n})`);
    }

    const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';

    const limitIdx = params.length + 1;
    const offsetIdx = params.length + 2;

    const [dataResult, countResult] = await Promise.all([
      pool.query(
        `SELECT transaction_id, timestamp, customer_id, amount, currency,
                merchant_category, distance_from_home_km, transactions_last_hour,
                hour_of_day, payment_method, risk_score, level, decision,
                source, alert_status
         FROM transactions
         ${where}
         ORDER BY ${sortColumn} ${sortOrder}, transaction_id
         LIMIT $${limitIdx} OFFSET $${offsetIdx}`,
        [...params, page_size, offset]
      ),
      pool.query(`SELECT COUNT(*) FROM transactions ${where}`, params),
    ]);

    const total = Number(countResult.rows[0].count);

    res.json({
      status: 'ok',
      page,
      page_size,
      total,
      total_pages: Math.ceil(total / page_size),
      data: dataResult.rows,
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ status: 'error', error: 'Internal server error' });
  }
});
// search api
router.get('/:id', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM transactions WHERE transaction_id = $1',
      [req.params.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Transaction not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Internal server error' });
  }
});



export default router;