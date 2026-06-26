import os
import time
from psycopg2.pool import ThreadedConnectionPool
from dotenv import load_dotenv

load_dotenv()

connection_string = os.getenv("DATABASE_URL")

# Limpiar parámetros incompatibles con psycopg2 como "schema=public"
if connection_string and "?" in connection_string:
    base_url, query = connection_string.split("?", 1)
    params = [p for p in query.split("&") if not p.startswith("schema=")]
    if params:
        connection_string = base_url + "?" + "&".join(params)
    else:
        connection_string = base_url

is_mock_database = False

# Historial en memoria para modo mock
mock_database = {
    "users": [{"id": "mock-user-uuid", "nombre": "Colaborador Alura", "email": "colaborador@alura.edu"}],
    "chats": [],
    "messages": []
}

pool = None
if connection_string:
    try:
        # Intentar conectar a Postgres
        pool = ThreadedConnectionPool(1, 15, connection_string)
        # Verificar la conexión
        conn = pool.getconn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
        pool.putconn(conn)
        print("[OK] [Base de Datos] Conexión exitosa a PostgreSQL.")
    except Exception as e:
        print("\n[WARNING] [Base de Datos] No se pudo conectar a PostgreSQL.")
        print("[WARNING] [Base de Datos] El servidor backend operará en MODO MOCK (Memoria temporal) leyendo archivos locales.")
        print("[WARNING] [Base de Datos] No necesitas levantar PostgreSQL para realizar pruebas rápidas.\n")
        is_mock_database = True
else:
    print("\n[WARNING] [Base de Datos] DATABASE_URL no configurada. Operando en MODO MOCK.\n")
    is_mock_database = True

def db_query(query: str, params: tuple = None) -> list:
    if is_mock_database or not pool:
        return []
    
    conn = None
    try:
        start_time = time.time()
        conn = pool.getconn()
        with conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:  # Hay filas que retornar
                rows = cur.fetchall()
                colnames = [desc[0] for desc in cur.description]
                result = [dict(zip(colnames, row)) for row in rows]
            else:
                conn.commit()
                result = []
        pool.putconn(conn)
        duration = int((time.time() - start_time) * 1000)
        # print(f"[SQL Query] Ejecutada en {duration}ms | Filas devueltas: {len(result)}")
        return result
    except Exception as e:
        if conn:
            conn.rollback()
            try:
                pool.putconn(conn)
            except Exception:
                pass
        print(f"[SQL Error] Fallo al ejecutar consulta: {e}")
        raise e
