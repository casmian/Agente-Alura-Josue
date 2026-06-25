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
