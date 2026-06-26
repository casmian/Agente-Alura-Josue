import os
import sys
import time
import json
import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel

# Evitar errores de codificación en consolas Windows (CP1252)
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from db.client import db_query, is_mock_database
from agent.document_parser import parse_document_to_segments

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3.5-flash")
is_mock_ai = False
ai_client = None

if not GEMINI_API_KEY:
    print("\n[WARNING] [IA] La clave GEMINI_API_KEY no está configurada.")
    print("[WARNING] [IA] El servidor operará en MODO SIMULACIÓN DE IA (respuestas locales simuladas).\n")
    is_mock_ai = True
else:
    try:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
        print("[OK] [IA] Cliente google-genai inicializado con éxito.")
    except Exception as e:
        print(f"Error al inicializar cliente google-genai: {e}")
        is_mock_ai = True

class Evaluacion(BaseModel):
    index: int
    score: int
    motivo: str

class RerankResult(BaseModel):
    evaluaciones: list[Evaluacion]

def get_document_category(file_name: str) -> str:
    lower_name = file_name.lower()
    if (
        'entorno' in lower_name or 
        'configuracion' in lower_name or 
        'onboarding' in lower_name or 
        'incidentes' in lower_name
    ):
        return 'Entorno'
    if (
        'estilo' in lower_name or 
        'practicas' in lower_name or 
        'frontend' in lower_name or 
        'backend' in lower_name
    ):
        return 'Estilo'
    if (
        'modulo' in lower_name or 
        'arquitectura' in lower_name or 
        'dominios' in lower_name
    ):
        return 'Arquitectura'
    return 'General'

def get_document_owner(category: str) -> str:
    if category == 'Entorno':
        return 'DevOps Lead / Tech Lead'
    elif category == 'Estilo':
        return 'Frontend & Backend Leads'
    elif category == 'Arquitectura':
        return 'Software Architect'
    else:
        return 'Comité de Documentación Corporativa'

def generate_query_embedding(query: str) -> list:
    if is_mock_ai or not ai_client:
        return [0.0] * 1536
    try:
        response = ai_client.models.embed_content(
            model="gemini-embedding-2",
            contents=query,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=1536
            )
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"Error al generar query embedding: {e}")
        raise e

def mock_keyword_rerank(query: str, candidates: list) -> list:
    query_words = [w.lower() for w in query.split() if len(w) > 3]
    for c in candidates:
        matches = 0
        for w in query_words:
            if w in c['contenido'].lower():
                matches += 1
        c['score'] = min(5 + matches, 10) if matches > 0 else 4
    return sorted(candidates, key=lambda x: x.get('score', 0), reverse=True)

def gemini_rerank(query: str, candidates: list) -> list:
    if not candidates:
        return []
    if len(candidates) == 1:
        candidates[0]['score'] = 10
        return candidates
        
    formatted_candidates = []
    for idx, c in enumerate(candidates):
        formatted_candidates.append(
            f"--- FRAGMENTO ID: {idx} (Categoría: {c['categoria']} | Ubicación: {c['ubicacion_exacta']}) ---\n{c['contenido']}"
        )
    formatted_block = "\n\n".join(formatted_candidates)
    
    prompt = f"""Actúas como un clasificador de relevancia técnica.
Evalúa la utilidad de los siguientes fragmentos para responder con precisión a la pregunta del colaborador.
Pregunta del Colaborador: "{query}"

Fragmentos de Documentos:
{formatted_block}

Asigna a cada FRAGMENTO ID una puntuación entera del 0 al 10 (donde 0 es completamente irrelevante y 10 responde directamente a la pregunta con exactitud)."""

    try:
        response = ai_client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=RerankResult
            )
        )
        
        if not response.text:
            return candidates
            
        data = json.loads(response.text)
        evaluaciones = data.get("evaluaciones", [])
        
        scores = {item["index"]: item["score"] for item in evaluaciones if "index" in item and "score" in item}
        for idx, c in enumerate(candidates):
            c['score'] = scores.get(idx, 0)
            
        # Filtrar candidatos que tengan score >= 5
        filtered = [c for c in candidates if c.get('score', 0) >= 5]
        return sorted(filtered, key=lambda x: x.get('score', 0), reverse=True)
    except Exception as e:
        print(f"Error en Gemini Reranker: {e}. Usando orden original de palabra clave.")
        return mock_keyword_rerank(query, candidates)

def assemble_context_block(chunks: list) -> str:
    if not chunks:
        return 'No se encontraron documentos relevantes en la base de conocimientos.'
        
    blocks = []
    for idx, chunk in enumerate(chunks):
        last_mod = chunk['ultima_actualizacion']
        if isinstance(last_mod, (datetime.datetime, datetime.date)):
            last_mod_str = last_mod.isoformat()
        else:
            last_mod_str = str(last_mod)
            
        header = f"""[FUENTE DE CONOCIMIENTO #{idx + 1}]
- Archivo: {chunk['documento_nombre']}
- Categoría: {chunk['categoria']}
- Ubicación Exacta: {chunk['ubicacion_exacta']}
- Responsable: {chunk['autor_responsable']}
- Última Actualización: {last_mod_str}"""
        blocks.append(f"{header}\nContenido:\n\"\"\"\n{chunk['contenido']}\n\"\"\"")
    return "\n\n=========================================\n\n".join(blocks)

def retrieve_relevant_context(query: str, category_filter: str = None, limit_candidates: int = 10, limit_final: int = 3) -> str:
    if is_mock_database:
        print("[RAG] Ejecutando búsqueda semántica local desde cache/archivos...")
        store_path = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "mock_db_vector_store.json")
        candidates = []
        
        if os.path.exists(store_path):
            try:
                with open(store_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for c in data:
                    if category_filter and c["categoria"] != category_filter:
                        continue
                    candidates.append({
                        "id": f"mock-{c['documento_nombre']}-{time.time()}",
                        "documento_nombre": c["documento_nombre"],
                        "categoria": c["categoria"],
                        "contenido": c["contenido"],
                        "ubicacion_exacta": c["ubicacion_exacta"],
                        "autor_responsable": c["autor_responsable"],
                        "ultima_actualizacion": datetime.datetime.fromisoformat(c["ultima_actualizacion"]),
                        "similitud": 1.0
                    })
            except Exception as e:
                print(f"[RAG Mock Store Error] Fallo al cargar cache local: {e}")
                candidates = []
                
        # Fallback si el cache está vacío o falló
        if not candidates:
            kb_dir = os.path.join(os.path.dirname(__file__), "..", "..", "knowledge-base")
            if os.path.exists(kb_dir):
                files = os.listdir(kb_dir)
                for idx, file in enumerate(files):
                    category = get_document_category(file)
                    if category_filter and category != category_filter:
                        continue
                    file_path = os.path.join(kb_dir, file)
                    try:
                        segments = parse_document_to_segments(file_path)
                        stat = os.stat(file_path)
                        mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                        for s_idx, seg in enumerate(segments):
                            candidates.append({
                                "id": f"mock-{file}-{idx}-{s_idx}",
                                "documento_nombre": file,
                                "categoria": category,
                                "contenido": seg["content"],
                                "ubicacion_exacta": seg["location"],
                                "autor_responsable": get_document_owner(category),
                                "ultima_actualizacion": mtime,
                                "similitud": 1.0
                            })
                    except Exception as e:
                        print(f"[RAG Mock] Error leyendo {file}: {e}")
        
        if not candidates:
            return ""
            
        if is_mock_ai:
            reranked = mock_keyword_rerank(query, candidates)
        else:
            reranked = gemini_rerank(query, candidates)
            
        final_chunks = reranked[:limit_final]
        return assemble_context_block(final_chunks)
        
    query_vector = generate_query_embedding(query)
    vector_string = "[" + ",".join(map(str, query_vector)) + "]"
    
    if category_filter:
        sql = """SELECT id, documento_nombre, categoria, contenido, ubicacion_exacta, autor_responsable, ultima_actualizacion,
                 1 - (embedding <=> %s) AS similitud
                 FROM document_chunks
                 WHERE categoria = %s
                 ORDER BY embedding <=> %s
                 LIMIT %s"""
        params = (vector_string, category_filter, vector_string, limit_candidates)
    else:
        sql = """SELECT id, documento_nombre, categoria, contenido, ubicacion_exacta, autor_responsable, ultima_actualizacion,
                 1 - (embedding <=> %s) AS similitud
                 FROM document_chunks
                 ORDER BY embedding <=> %s
                 LIMIT %s"""
        params = (vector_string, vector_string, limit_candidates)
        
    db_result = db_query(sql, params)
    
    candidates = []
    for row in db_result:
        candidates.append({
            "id": str(row["id"]),
            "documento_nombre": row["documento_nombre"],
            "categoria": row["categoria"],
            "contenido": row["contenido"],
            "ubicacion_exacta": row["ubicacion_exacta"],
            "autor_responsable": row["autor_responsable"],
            "ultima_actualizacion": row["ultima_actualizacion"],
            "similitud": float(row["similitud"])
        })
        
    if not candidates:
        return ""
        
    if is_mock_ai:
        reranked = mock_keyword_rerank(query, candidates)
    else:
        reranked = gemini_rerank(query, candidates)
        
    final_chunks = reranked[:limit_final]
    return assemble_context_block(final_chunks)
