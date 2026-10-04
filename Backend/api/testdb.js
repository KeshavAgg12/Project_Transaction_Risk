import { pool } from './db.js'

const result = await pool.query('SELECT COUNT(*) FROM transactions')
console.log(result.rows)
await pool.end()


