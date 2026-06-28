import os
import sys
import warnings
import urllib.request
import json
import urllib.parse
import threading
import http.server
import socketserver

# Silenciar todas las advertencias y avisos de librerías externas (ej. deprecaciones de LangChain)
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage

# Codificación UTF-8 para evitar errores en consolas Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
        sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
    except AttributeError:
        pass

load_dotenv()
clave_api = os.getenv("GEMINI_API_KEY")
if not clave_api:
    print("[ERROR] No se encontró GEMINI_API_KEY en el archivo .env")
    sys.exit(1)

# Iniciar servidor web de salud para plataformas como Render
def iniciar_servidor_salud():
    port = int(os.getenv("PORT", 8080))
    class HealthHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Agente Alura está corriendo correctamente en segundo plano.".encode("utf-8"))
        
        def log_message(self, format, *args):
            # Evitar saturar la consola de Render con logs de peticiones de salud
            pass

    try:
        with socketserver.TCPServer(("", port), HealthHandler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        pass

if os.getenv("PORT") or os.getenv("RENDER"):
    threading.Thread(target=iniciar_servidor_salud, daemon=True).start()


# Leer todos los documentos de la base de conocimientos
contexto = ""
directorio = "base-conocimiento"
if os.path.exists(directorio):
    for archivo in os.listdir(directorio):
        ruta = os.path.join(directorio, archivo)
        if os.path.isfile(ruta) and archivo.endswith(('.md', '.csv', '.txt')):
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    contexto += f"\n--- ARCHIVO: {archivo} ---\n{f.read()}\n"
            except Exception as e:
                print(f"[ADVERTENCIA] Error al leer {archivo}: {e}")
else:
    print(f"[ADVERTENCIA] No existe la carpeta '{directorio}'.")


# Definición de herramientas del Agente
@tool
def buscar_en_internet(query: str) -> str:
    """Busca información técnica general de programación, APIs o explicaciones conceptuales en Wikipedia en español. Úsalo cuando la duda técnica del alumno no esté respondida en los manuales de Neouniverse."""
    try:
        url = f"https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json&utf8="
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            resultados = data.get('query', {}).get('search', [])
            if resultados:
                snippets = []
                for r in resultados[:3]:
                    title = r.get('title')
                    snippet = r.get('snippet').replace("<span class=\"searchmatch\">", "").replace("</span>", "")
                    snippets.append(f"- {title}: {snippet}")
                return "\n".join(snippets)
            return "No se encontraron resultados en Wikipedia."
    except Exception as e:
        return f"Error al realizar la búsqueda web: {e}"


@tool
def ejecutar_codigo_sandbox(codigo: str) -> str:
    """Ejecuta código de Python de forma local en un entorno controlado para validar las soluciones a los retos o comprobar sintaxis técnica de los alumnos. Devuelve la salida en consola (stdout) o los errores del intérprete."""
    from io import StringIO
    
    # Redirigir stdout para capturar la salida
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    
    scope_local = {}
    
    try:
        # Ejecutar el código en el scope local limitado
        exec(codigo, {"__builtins__": __builtins__}, scope_local)
        sys.stdout = old_stdout
        salida = redirected_output.getvalue()
        return salida if salida.strip() else "El código se ejecutó correctamente sin imprimir salidas en consola."
    except Exception as e:
        sys.stdout = old_stdout
        return f"Error durante la ejecución del código: {type(e).__name__}: {e}"


# Inicialización de Gemini y Configuración del Agente Reactivo
print("Cargando base de conocimientos e inicializando el agente...")
try:
    # Inicializar el modelo LLM de Google
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=clave_api,
        temperature=0.2
    )
    
    # Lista de herramientas
    tools = [buscar_en_internet, ejecutar_codigo_sandbox]
    
    # Enlazar herramientas al modelo LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # Plantilla de Prompt ReAct con soporte para historial
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "Actúas como 'Agente Alura', un mentor técnico y asistente de onboarding inteligente e interactivo para nuevos desarrolladores que ingresan a la compañía Neouniverse.\n\n"
            "Tu misión principal es acelerar la adaptación de los nuevos desarrolladores al ritmo de trabajo de la empresa. Tus capacidades y responsabilidades clave:\n"
            "1. Mentor de Onboarding Técnico: Explica las directrices, arquitecturas de microservicios, guías de estilo, flujos de trabajo (Git flow, cómo hacer commits, estándares de calidad) y tecnologías que se utilizan en Neouniverse. Si el desarrollador te lo solicita, propónle pequeños retos técnicos o de configuración acordes a los estándares de la empresa y evalúa sus soluciones de código utilizando la herramienta 'ejecutar_codigo_sandbox'.\n"
            "2. Guía de Adaptación: Analiza el perfil, dudas y necesidades del desarrollador recién ingresado para aconsejarle qué manuales de onboarding, arquitecturas, políticas de QA o procesos internos de Neouniverse debe consultar a continuación.\n"
            "3. Compañero de Consultas (RAG): Responde preguntas sobre el funcionamiento técnico y operativo de Neouniverse basándote estrictamente en los manuales de la base de conocimiento provistos. Si la información no está en los manuales pero es una consulta técnica general de desarrollo (sintaxis de lenguajes, APIs generales), utiliza la herramienta 'buscar_en_internet' para guiarle. Si la consulta es específica de Neouniverse (temas de RRHH propios, políticas internas o arquitectura específica) y no se encuentra en los manuales provistos, di amablemente: 'Lo siento, la información solicitada no se encuentra en la base de conocimientos de Neouniverse. Por favor, comunícate en el canal de Slack #soporte-arquitectura.'\n\n"
            "Reglas Generales:\n"
            "- Responde de forma clara, directa, amigable y estructurada en Markdown.\n"
            "- Asume el conocimiento de los manuales como propio de forma natural, sin citar nombres de archivos ni secciones.\n"
            "- No muestres metadatos de archivos ni secciones de referencias.\n\n"
            "DOCUMENTOS DE ONBOARDING DE NEOUNIVERSE:\n{contexto}"
        )),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

    
    # Cadena LCEL con el modelo enlazado a las herramientas
    chain = (
        {
            "contexto": lambda x: contexto,
            "input": lambda x: x["input"],
            "history": lambda x: x["history"]
        }
        | prompt
        | llm_with_tools
    )
    
    # Historial de mensajes en memoria local
    historial = InMemoryChatMessageHistory()
    
except Exception as e:
    print(f"[ERROR] No se pudo inicializar el Agente Alura: {e}")
    sys.exit(1)

def limpiar_contenido(content) -> str:
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        textos = []
        for bloque in content:
            if isinstance(bloque, dict) and "text" in bloque:
                textos.append(bloque["text"])
            elif isinstance(bloque, str):
                textos.append(bloque)
        return "".join(textos)
    return str(content)

print("\n" + "=" * 55)
# Título limpio del chat interactivo
print("🤖 Agente Alura — Tutor Técnico Interactivo 🤖")
print("=" * 55)
print("¡Hola! Soy tu tutor técnico de Neouniverse. Escribe 'salir' para terminar.\n")

# Bucle interactivo
while True:
    try:
        pregunta = input("\nTú: ").strip()
        if not pregunta:
            continue
        if pregunta.lower() in ["salir", "exit", "quit"]:
            print("\n¡Hasta luego! Que tengas un excelente día de desarrollo.")
            break
        
        print("Agente Alura está pensando...")
        
        # Invocar la cadena pasándole la consulta y el historial de mensajes
        mensajes_previos = historial.messages
        respuesta = chain.invoke({
            "input": pregunta,
            "history": mensajes_previos
        })
        
        # Guardar la pregunta del usuario en el historial
        historial.add_user_message(pregunta)
        
        # Si el modelo solicita ejecutar una herramienta
        if respuesta.tool_calls:
            # Añadir la respuesta parcial del LLM al historial
            historial.add_message(respuesta)
            
            for tool_call in respuesta.tool_calls:
                nombre_tool = tool_call["name"]
                argumentos = tool_call["args"]
                tool_id = tool_call["id"]
                
                # Ejecutar la herramienta correspondiente
                resultado_tool = ""
                if nombre_tool == "buscar_en_internet":
                    resultado_tool = buscar_en_internet.invoke(argumentos)
                elif nombre_tool == "ejecutar_codigo_sandbox":
                    resultado_tool = ejecutar_codigo_sandbox.invoke(argumentos)
                
                # Devolver el resultado de la herramienta al LLM mediante un ToolMessage
                tool_message = ToolMessage(
                    content=str(resultado_tool),
                    tool_call_id=tool_id,
                    name=nombre_tool
                )
                historial.add_message(tool_message)
            
            # Volver a invocar el modelo con el historial que ahora incluye el ToolMessage
            respuesta_final = llm_with_tools.invoke(historial.messages)
            historial.add_message(respuesta_final)
            print(f"\nAgente Alura:\n{limpiar_contenido(respuesta_final.content)}")
        else:
            # Si no requirió herramientas, añadir la respuesta directa del LLM al historial
            historial.add_message(respuesta)
            print(f"\nAgente Alura:\n{limpiar_contenido(respuesta.content)}")
            
        print("-" * 55)
        
    except (KeyboardInterrupt, EOFError):
        print("\n\n¡Hasta luego! Conversación terminada.")
        break
    except Exception as e:
        print(f"\n⚠️ Ocurrió un problema: {e}")



