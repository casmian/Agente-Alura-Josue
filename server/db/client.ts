import { Pool } from 'pg';
import * as dotenv from 'dotenv';

dotenv.config();

const connectionString = process.env.DATABASE_URL;

if (!connectionString) {
  throw new Error('La variable de entorno DATABASE_URL no está configurada.');
}

// Crear un pool de conexiones reutilizable
export const dbPool = new Pool({
  connectionString,
  max: process.env.DB_POOL_MAX ? parseInt(process.env.DB_POOL_MAX) : 10,
  min: process.env.DB_POOL_MIN ? parseInt(process.env.DB_POOL_MIN) : 2,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Helper para consultas rápidas
export async function dbQuery(text: string, params?: any[]) {
  const start = Date.now();
  const res = await dbPool.query(text, params);
  const duration = Date.now() - start;
  
  if (process.env.NODE_ENV !== 'production') {
    console.debug('Consulta ejecutada:', { text, duration, rowsCount: res.rowCount });
  }
  
  return res;
}
