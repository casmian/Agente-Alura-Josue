import os
import sys
import uuid
import time
import datetime

# Evitar errores de codificación en consolas Windows (CP1252)
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
from google.genai import types
from dotenv import load_dotenv

from db.client import db_query, is_mock_database, mock_database
from agent.retrieval_engine import retrieve_relevant_context, is_mock_ai, ai_client
from utils.execution_logger import log_execution

load_dotenv()

GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3.5-flash")

def fetch_chat_history(chat_id: str) -> list:
    """
    Recupera el historial de chat guardado en PostgreSQL o en memoria.
    """
    if is_mock_database:
        return [
            {"role": m["role"], "content": m["content"]}
            for m in mock_database["messages"]
            if m["chatId"] == chat_id
        ]

    try:
        rows = db_query(
            "SELECT role, content FROM messages WHERE chat_id = %s ORDER BY created_at ASC",
            (chat_id,)
        )
        return [{"role": row["role"], "content": row["content"]} for row in rows]
    except Exception as e:
        print(f"Error al recuperar el historial de chat: {e}")
        return []

def save_message(chat_id: str, role: str, content: str):
    """
    Persiste un mensaje individual en la base de datos o en memoria.
    """
    if is_mock_database:
        mock_database["messages"].append({
            "chatId": chat_id,
            "role": role,
            "content": content,
            "created_at": datetime.datetime.now()
        })
        return

    try:
        db_query(
            "INSERT INTO messages (chat_id, role, content) VALUES (%s, %s, %s)",
            (chat_id, role, content)
        )
    except Exception as e:
        print(f"Error al persistir mensaje en base de datos: {e}")

def create_new_chat_session(user_id: str, title: str = 'Nueva Consulta') -> str:
    """
    Crea una nueva sesión de chat en base de datos o en memoria.
    """
    if is_mock_database:
        new_id = f"mock-chat-{str(uuid.uuid4())[:8]}"
        mock_database["chats"].append({
            "id": new_id,
            "user_id": user_id,
            "titulo": title,
            "created_at": datetime.datetime.now()
        })
        return new_id

    try:
        user_check = db_query("SELECT id FROM users LIMIT 1")
        db_user_id = user_id
        if not user_check:
            print("No se encontraron usuarios en la BD. Creando usuario por defecto...")
            new_user = db_query(
                "INSERT INTO users (nombre, email) VALUES ('Colaborador Alura', 'colaborador@alura.edu') RETURNING id"
            )
            db_user_id = str(new_user[0]["id"])
            
        res = db_query(
            "INSERT INTO chats (user_id, titulo) VALUES (%s, %s) RETURNING id",
            (db_user_id, title)
        )
        return str(res[0]["id"])
    except Exception as e:
        print(f"Error al crear sesión de chat: {e}")
        return str(uuid.uuid4())

def run_agent_conversation(user_id: str, message: str, chat_id: str = None, category_filter: str = None) -> dict:
    """
    Orquesta la conversación RAG y persiste el historial y los logs de auditoría.
    """
    start_time = time.time()
    
    active_chat_id = chat_id
    if not active_chat_id:
        title = message[:40] + "..." if len(message) > 40 else message
        active_chat_id = create_new_chat_session(user_id, title)
        
    history = fetch_chat_history(active_chat_id)
    context_block = retrieve_relevant_context(message, category_filter)
    system_prompt = f"""Actúas como el 'Agente Alura', un asistente cognitivo de nivel empresarial y mentor técnico para los colaboradores de la compañía Neouniverse.
Tu misión es resolver dudas técnicas de onboarding, guías de estilos de código, arquitectura de microservicios y protocolos operativos de Neouniverse con base EXCLUSIVA en los documentos adjuntos en el bloque de contexto.

REGLAS DE GENERACIÓN DE RESPUESTA:
1. Responde de forma clara, técnica, estructurada en Markdown y constructiva.
2. Si el bloque de contexto contiene la respuesta, debes responder basándote estrictamente en él.
3. CONTROL DE ALUCINACIONES: Si el contexto no contiene la información para responder la pregunta, di textualmente: "Lo siento, la información solicitada no se encuentra en la base de conocimientos de Neouniverse." y sugiere amablemente al usuario contactar al canal corporativo de Slack de soporte técnico (#soporte-arquitectura). No intentes inventar respuestas.
4. TUTOR DE CÓDIGO CONSTRUCTIVO: Cuando se te solicite evaluar o ayudar con código, guíales de forma socrática, explica el concepto de fondo, pero no les des el código ya resuelto.
5. RESPUESTA DIRECTA, NATURAL Y LIMPIA: Responde de forma directa y fluida a la consulta técnica del usuario sin hacer comentarios meta-documentales o explicaciones sobre los archivos (evita usar frases como "según el archivo tal", "en base a la documentación que tengo", "puedes encontrar esa información en la carpeta X"). No incluyas secciones de referencias, ni listados de fuentes, ni nombres de archivos. Asume el conocimiento como propio en base a la información que tienes y explícalo directamente de forma limpia.

---
CONTEXTO RELEVANTE DE NEOUNIVERSE:
{context_block}"""

    reply = ""
    if is_mock_ai or not ai_client:
        print("[Orchestrator Mock] Generando respuesta local basada en el contexto...")
        if not context_block or "No se encontraron documentos" in context_block:
            reply = 'Lo siento, la información solicitada no se encuentra en la base de conocimientos de Neouniverse. Por favor, contacta con el canal de Slack #soporte-arquitectura.'
        else:
            import re
            fuentes = re.findall(
                r"- Archivo: (.*?)\n- Categoría: (.*?)\n- Ubicación Exacta: (.*?)\n- Responsable: (.*?)\n- Última Actualización: (.*?)\nContenido:\n\"\"\"(.*?)\"\"\"",
                context_block,
                re.DOTALL
            )
            
            if fuentes:
                reply = fuentes[0][5].strip()
            else:
                reply = "Lo siento, la información no pudo ser extraída correctamente del contexto."
    else:
        try:
            chat_contents = []
            
            for h in history:
                role = "user" if h["role"] == "user" else "model"
                chat_contents.append(
                    types.Content(role=role, parts=[types.Part.from_text(text=h["content"])])
                )
                
            chat_contents.append(
                types.Content(role="user", parts=[types.Part.from_text(text=message)])
            )
            
            response = ai_client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=chat_contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt
                )
            )
            reply = response.text or "Error: No se recibió respuesta del modelo."
        except Exception as e:
            print(f"Fallo en generación de contenido de Gemini: {e}")
            reply = "⚠️ Ocurrió un error al intentar conectarse con la API de Gemini."
            
    save_message(active_chat_id, 'user', message)
    save_message(active_chat_id, 'model', reply)
    
    latency_ms = int((time.time() - start_time) * 1000)
    log_execution(active_chat_id, message, context_block, reply, latency_ms)
    
    return {
        "reply": reply,
        "chatId": active_chat_id
    }
