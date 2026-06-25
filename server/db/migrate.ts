import * as fs from 'fs';
import * as path from 'path';
import { dbQuery, dbPool } from './client';

async function runMigrations() {
  console.log('Iniciando migraciones de base de datos...');
  
  const schemaPath = path.join(__dirname, 'schema.sql');
  
  if (!fs.existsSync(schemaPath)) {
    console.error(`No se encontró el archivo de esquema en: ${schemaPath}`);
    process.exit(1);
  }
  
  const sql = fs.readFileSync(schemaPath, 'utf8');
  
  try {
    // Ejecutar todo el script de base de datos
    await dbQuery(sql);
    console.log('¡Migraciones completadas exitosamente!');
  } catch (error) {
    console.error('Error crítico al ejecutar migraciones de base de datos:', error);
  } finally {
    // Cerrar el pool para que finalice el script
    await dbPool.end();
  }
}

runMigrations();
