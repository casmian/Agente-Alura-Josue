import os
import sys
import datetime
import json

# Evitar errores de codificación en consolas Windows (CP1252)
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Permitir importaciones de carpetas superiores
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from google.genai import types
from db.client import db_query, is_mock_database
from agent.document_parser import parse_document_to_segments, clean_text_content
from agent.retrieval_engine import get_document_category, get_document_owner, ai_client, is_mock_ai

def generate_embedding(text: str) -> list:
    """
    Llama al SDK de Gemini para obtener el embedding del texto,
    o retorna un vector de ceros en modo simulación.
    """
    if is_mock_ai or not ai_client:
        return [0.0] * 1536
    try:
        response = ai_client.models.embed_content(
            model="gemini-embedding-2",
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=1536
            )
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"Error al generar embedding en ingesta: {e}")
        raise e

def sub_chunk_segment(text: str, max_chunk_size: int = 1000, overlap: int = 150) -> list:
    """
    Subdivide texto largo manteniendo solapamiento para mejorar la calidad del RAG.
    """
    if len(text) <= max_chunk_size:
        return [text]
        
    sub_chunks = []
    current_index = 0
    while current_index < len(text):
        end_index = current_index + max_chunk_size
        if end_index < len(text):
            last_space = text.rfind(' ', current_index, end_index)
            if last_space > current_index:
                end_index = last_space
                
        sub_chunk = text[current_index:end_index].strip()
        if sub_chunk:
            sub_chunks.append(sub_chunk)
            
        current_index = end_index - overlap
        if current_index >= len(text) or max_chunk_size <= overlap:
            break
            
    return sub_chunks

def start_ingestion():
    print("Iniciando pipeline de ingesta y extracción RAG en Python...")
    
    kb_dir = os.path.join(os.path.dirname(__file__), "..", "..", "knowledge-base")
    if not os.path.exists(kb_dir):
        print(f"El directorio de base de conocimientos no existe: {kb_dir}")
        sys.exit(1)
        
    files = os.listdir(kb_dir)
    print(f"Archivos detectados en knowledge-base: {', '.join(files)}")
    
    mock_store = []
    
    # Limpiar base de datos si está activa
    if not is_mock_database:
        try:
            print("Limpiando base de datos de fragmentos anteriores...")
            db_query("DELETE FROM document_chunks;")
        except Exception as e:
            print(f"No se pudo limpiar la base de datos: {e}")
            sys.exit(1)
            
    for file in files:
        file_path = os.path.join(kb_dir, file)
        category = get_document_category(file)
        owner = get_document_owner(category)
        
        stat = os.stat(file_path)
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
        
        print(f"\nProcesando archivo: '{file}'")
        print(f"- Categoría: {category}")
        print(f"- Responsable: {owner}")
        print(f"- Última Actualización: {mtime.isoformat()}")
        
        try:
            segments = parse_document_to_segments(file_path)
            print(f"Documento dividido originalmente en {len(segments)} segmentos estructurales.")
            
            chunk_counter = 0
            for seg in segments:
                clean_content = clean_text_content(seg["content"])
                if not clean_content:
                    continue
                    
                sub_chunks = sub_chunk_segment(clean_content, 1000, 150)
                for idx, chunk in enumerate(sub_chunks):
                    chunk_counter += 1
                    location = f"{seg['location']} (Parte {idx + 1}/{len(sub_chunks)})" if len(sub_chunks) > 1 else seg["location"]
                    
                    print(f"Indexando fragmento {chunk_counter} ({location})...")
                    
                    # Generar embedding
                    vector = generate_embedding(chunk)
                    
                    if is_mock_database:
                        mock_store.append({
                            "documento_nombre": file,
                            "categoria": category,
                            "contenido": chunk,
                            "ubicacion_exacta": location,
                            "autor_responsable": owner,
                            "ultima_actualizacion": mtime.isoformat(),
                            "embedding": vector
                        })
                    else:
                        vector_string = "[" + ",".join(map(str, vector)) + "]"
                        db_query(
                            """INSERT INTO document_chunks 
                               (documento_nombre, categoria, contenido, ubicacion_exacta, autor_responsable, ultima_actualizacion, embedding)
                               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                            (file, category, chunk, location, owner, mtime, vector_string)
                        )
                        
            print(f"¡Archivo '{file}' indexado exitosamente con {chunk_counter} fragmentos!")
        except Exception as e:
            print(f"Error crítico procesando el archivo '{file}': {e}")
            
    # Guardar store local si estamos en mock
    if is_mock_database:
        store_path = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "mock_db_vector_store.json")
        os.makedirs(os.path.dirname(store_path), exist_ok=True)
        with open(store_path, "w", encoding="utf-8") as f:
            json.dump(mock_store, f, ensure_ascii=False, indent=2)
        print(f"\n[WARNING] [Base de Datos Mock] Fragmentos locales guardados en cache local: logs/mock_db_vector_store.json")
        
    print('\n=========================================')
    print('¡Pipeline de ingesta finalizado con éxito!')
    print('=========================================')

if __name__ == "__main__":
    start_ingestion()
