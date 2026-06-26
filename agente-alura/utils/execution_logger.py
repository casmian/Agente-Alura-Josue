import os
import json
import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
LOG_FILE = os.path.join(LOG_DIR, "execution_log.jsonl")

def log_execution(chat_id: str, query: str, context: str, response: str, latency_ms: int):
    """
    Registra una transacción RAG en formato JSON Lines.
    """
    try:
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR, exist_ok=True)
            
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "chatId": chat_id,
            "query": query,
            "context": context,
            "response": response,
            "latencyMs": latency_ms
        }
        
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
        print(f"[Logger] Log guardado en local: logs/execution_log.jsonl ({latency_ms}ms)")
    except Exception as e:
        print(f"[Logger Error] Fallo al escribir log local: {e}")

def read_logs(limit: int = 50) -> list:
    """
    Retorna los últimos registros de ejecución en orden inverso (más recientes primero).
    """
    try:
        if not os.path.exists(LOG_FILE):
            return []
            
        logs = []
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        logs.append(json.loads(line))
                    except Exception:
                        pass
        return list(reversed(logs))[:limit]
    except Exception as e:
        print(f"[Logger Error] Fallo al leer logs locales: {e}")
        return []
