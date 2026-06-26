import os
import sys
from client import db_query, is_mock_database, pool

# Evitar errores de codificación en consolas Windows (CP1252)
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def run_migrations():
    print("Iniciando migraciones de base de datos en Python...")
    
    if is_mock_database or not pool:
        print("[WARNING] [Base de Datos] Operando en Modo Mock. No se ejecutarán migraciones.")
        return
        
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    if not os.path.exists(schema_path):
        print(f"No se encontró el archivo de esquema en: {schema_path}")
        return
        
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()
        
    try:
        db_query(sql)
        print("¡Migraciones de base de datos completadas exitosamente!")
    except Exception as e:
        print(f"Error crítico al ejecutar migraciones de base de datos: {e}")
    finally:
        if pool:
            pool.closeall()

if __name__ == "__main__":
    run_migrations()
