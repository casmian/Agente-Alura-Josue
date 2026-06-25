import * as fs from 'fs';
import * as path from 'path';

export interface LogEntry {
  timestamp: string;
  chatId: string;
  query: string;
  context: string;
  response: string;
  latencyMs: number;
}

const logDir = path.join(__dirname, '..', '..', 'logs');
const logFile = path.join(logDir, 'execution_log.jsonl');

/**
 * Registra una transacción de ejecución de RAG en un archivo local en formato JSON Lines (.jsonl)
 */
export function logExecution(entry: LogEntry): void {
  try {
    // Asegurar la existencia del directorio de logs
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }

    // Convertir entrada a una sola línea de JSON y añadir salto de línea
    const logLine = JSON.stringify(entry) + '\n';
    
    // Anexar al archivo (Append mode)
    fs.appendFileSync(logFile, logLine, 'utf8');
    
    if (process.env.NODE_ENV !== 'production') {
      console.log(`[Logger] Log guardado en local: logs/execution_log.jsonl (${entry.latencyMs}ms)`);
    }
  } catch (error) {
    console.error('[Logger] Error al escribir en el archivo de registro local:', error);
  }
}

/**
 * Lee los últimos registros de ejecución en formato JSON Lines
 */
export function readLogs(limit: number = 50): LogEntry[] {
  try {
    if (!fs.existsSync(logFile)) {
      return [];
    }
    const fileContent = fs.readFileSync(logFile, 'utf8');
    const lines = fileContent.trim().split('\n').filter(line => line.trim() !== '');
    
    const logs: LogEntry[] = lines.map(line => {
      try {
        return JSON.parse(line);
      } catch (e) {
        return null;
      }
    }).filter(entry => entry !== null) as LogEntry[];

    // Devolver invertido para tener el más reciente primero, limitado a 'limit'
    return logs.slice(-limit).reverse();
  } catch (error) {
    console.error('[Logger] Error al leer el archivo de registros local:', error);
    return [];
  }
}

