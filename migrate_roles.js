'use strict';
require('dotenv').config();
const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});

const steps = [
  `DO $x$
   BEGIN
     CREATE TYPE user_role AS ENUM ('admin','radiologist','technician','frontdesk','manager');
   EXCEPTION WHEN duplicate_object THEN NULL;
   END $x$`,
  `ALTER TABLE users ADD COLUMN IF NOT EXISTS role user_role NOT NULL DEFAULT 'frontdesk'`,
  `CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)`,
];

(async () => {
  for (const sql of steps) {
    await pool.query(sql);
    console.log('OK:', sql.trim().slice(0, 60));
  }
  console.log('Migration complete.');
  await pool.end();
})().catch(err => {
  console.error('Migration failed:', err.message);
  pool.end();
  process.exit(1);
});
