import { Pool } from 'pg';
import * as dotenv from 'dotenv';

dotenv.config();

const connectionString = process.env.DATABASE_URL;

if (!connectionString) {
  throw new Error('La variable de entorno DATABASE_URL no está configurada.');
}

// Bandera global para modo fallback sin base de datos
export let isMockDatabase = false;

// Historial en memoria para modo mock
export const mockDatabase: {
  users: any[];
  chats: any[];
  messages: any[];
} = {
  users: [{ id: 'mock-user-uuid', nombre: 'Colaborador Alura', email: 'colaborador@alura.edu' }],
  chats: [],
  messages: []
};

export const dbPool = new Pool({
  connectionString,
  max: process.env.DB_POOL_MAX ? parseInt(process.env.DB_POOL_MAX) : 10,
  min: process.env.DB_POOL_MIN ? parseInt(process.env.DB_POOL_MIN) : 2,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Probar conexión inicial de base de datos
dbPool.connect((err, client, release) => {
  if (err) {
    console.warn('\n⚠️  [Base de Datos] No se pudo conectar a PostgreSQL.');
    console.warn('⚠️  [Base de Datos] El servidor backend operará en MODO MOCK (Memoria temporal) leyendo archivos locales.');
    console.warn('⚠️  [Base de Datos] No necesitas levantar PostgreSQL para realizar pruebas rápidas.\n');
    isMockDatabase = true;
  } else {
    console.log('✅ [Base de Datos] Conexión exitosa a PostgreSQL.');
    release();
  }
});

// Helper para consultas rápidas
export async function dbQuery(text: string, params?: any[]) {
  if (isMockDatabase) {
    return { rows: [], rowCount: 0 };
  }

  const start = Date.now();
  const res = await dbPool.query(text, params);
  const duration = Date.now() - start;
  
  if (process.env.NODE_ENV !== 'production') {
    console.debug('Consulta ejecutada:', { text, duration, rowsCount: res.rowCount });
  }
  
  return res;
}
