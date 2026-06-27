import os
import sys
import warnings
import urllib.request
import json
import urllib.parse
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage

# Silenciar advertencias
warnings.filterwarnings("ignore")

load_dotenv()
clave_api = os.getenv("GEMINI_API_KEY")

# Cargar la base de conocimientos
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

# Herramientas del Agente
@tool
def buscar_en_internet(query: str) -> str:
    """Busca información técnica general de programación, APIs o explicaciones en Wikipedia en español. Úsalo si la duda técnica no está en los manuales."""
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
            return "No se encontraron resultados."
    except Exception as e:
        return f"Error de búsqueda: {e}"

@tool
def ejecutar_codigo_sandbox(codigo: str) -> str:
    """Ejecuta código de Python en un entorno controlado para validar retos o sintaxis. Devuelve la salida estándar."""
    from io import StringIO
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    scope_local = {}
    try:
        exec(codigo, {"__builtins__": __builtins__}, scope_local)
        sys.stdout = old_stdout
        salida = redirected_output.getvalue()
        return salida if salida.strip() else "Código ejecutado correctamente sin salidas."
    except Exception as e:
        sys.stdout = old_stdout
        return f"Error: {type(e).__name__}: {e}"

# Configuración de Flask
app = Flask(__name__)
historiales_por_sesion = {}

# Inicializar modelo de LangChain
def obtener_cadena_agente():
    if not clave_api:
        raise ValueError("Falta GEMINI_API_KEY")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=clave_api,
        temperature=0.2
    )
    tools = [buscar_en_internet, ejecutar_codigo_sandbox]
    llm_with_tools = llm.bind_tools(tools)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "Actúas como 'Agente Alura', un mentor técnico y asistente de onboarding inteligente para desarrolladores de Neouniverse.\n"
            "Tus responsabilidades:\n"
            "1. Mentor de Onboarding: Explica estándares, arquitecturas de microservicios y flujos. Propón retos de código y evalúalos con 'ejecutar_codigo_sandbox'.\n"
            "2. Guía de Adaptación: Sugiere qué manuales internos leer.\n"
            "3. RAG: Responde basándote estrictamente en los manuales provistos. Para dudas técnicas generales, usa 'buscar_en_internet'. Si es específico de Neouniverse y no está en los manuales, di: 'Lo siento, la información no se encuentra en la base de conocimientos de Neouniverse. Por favor, comunícate en el canal #soporte-arquitectura.'\n\n"
            "Reglas:\n"
            "- Responde amigable y estructurado en Markdown.\n"
            "- No cites nombres de archivos de manuales.\n\n"
            "DOCUMENTOS:\n{contexto}"
        )),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])
    
    chain = (
        {
            "contexto": lambda x: contexto,
            "input": lambda x: x["input"],
            "history": lambda x: x["history"]
        }
        | prompt
        | llm_with_tools
    )
    return chain, llm_with_tools

# HTML/CSS Embebido con Diseño Premium e Interfaz de Chat
HTML_CHAT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agente Alura — Mentor de Onboarding</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-gradient: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #1e1b4b 100%);
            --panel-bg: rgba(17, 24, 39, 0.7);
            --border-color: rgba(255, 255, 255, 0.08);
            --accent-glow: linear-gradient(135deg, #6366f1, #3b82f6);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background: var(--bg-gradient);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }

        .chat-container {
            width: 90%;
            max-width: 900px;
            height: 85vh;
            background: var(--panel-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: 24px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 40px rgba(99, 102, 241, 0.1);
        }

        .chat-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .agent-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .agent-avatar {
            width: 44px;
            height: 44px;
            background: var(--accent-glow);
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 22px;
            box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
        }

        .agent-status-container {
            display: flex;
            flex-direction: column;
        }

        .agent-name {
            font-weight: 700;
            font-size: 1.1rem;
            letter-spacing: 0.5px;
        }

        .agent-status {
            font-size: 0.8rem;
            color: #10b981;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background-color: #10b981;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 8px #10b981;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        .chat-messages {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .chat-messages::-webkit-scrollbar {
            width: 6px;
        }

        .chat-messages::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }

        .message {
            max-width: 80%;
            padding: 14px 18px;
            border-radius: 18px;
            font-size: 0.95rem;
            line-height: 1.5;
            word-wrap: break-word;
            animation: fadeIn 0.3s ease-out forwards;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message-user {
            align-self: flex-end;
            background: var(--accent-glow);
            color: white;
            border-bottom-right-radius: 4px;
            box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3);
        }

        .message-agent {
            align-self: flex-start;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            border-bottom-left-radius: 4px;
        }

        .message-agent p {
            margin-bottom: 8px;
        }
        .message-agent p:last-child {
            margin-bottom: 0;
        }

        .message-agent pre {
            background: rgba(0, 0, 0, 0.4);
            padding: 12px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 10px 0;
            border: 1px solid rgba(255, 255, 255, 0.05);
            font-family: monospace;
            font-size: 0.85rem;
        }

        .message-agent code {
            font-family: monospace;
            background: rgba(255, 255, 255, 0.1);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.9rem;
        }

        .chat-input-area {
            padding: 20px 24px;
            border-top: 1px solid var(--border-color);
            display: flex;
            gap: 12px;
            background: rgba(10, 15, 26, 0.4);
            border-bottom-left-radius: 24px;
            border-bottom-right-radius: 24px;
        }

        .chat-input {
            flex: 1;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 14px 18px;
            color: white;
            font-family: inherit;
            font-size: 0.95rem;
            outline: none;
            transition: all 0.2s;
        }

        .chat-input:focus {
            border-color: #6366f1;
            background: rgba(255, 255, 255, 0.07);
            box-shadow: 0 0 10px rgba(99, 102, 241, 0.2);
        }

        .send-btn {
            background: var(--accent-glow);
            border: none;
            color: white;
            border-radius: 14px;
            padding: 0 24px;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }

        .send-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
        }

        .send-btn:active {
            transform: translateY(0);
        }

        .typing-indicator {
            display: none;
            align-self: flex-start;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            padding: 14px 20px;
            border-radius: 18px;
            border-bottom-left-radius: 4px;
        }

        .dots {
            display: flex;
            gap: 5px;
            align-items: center;
            height: 10px;
        }

        .dot {
            width: 8px;
            height: 8px;
            background: #6366f1;
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out both;
        }

        .dot:nth-child(1) { animation-delay: -0.32s; }
        .dot:nth-child(2) { animation-delay: -0.16s; }

        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1.0); }
        }
    </style>
</head>
<body>

    <div class="chat-container">
        <div class="chat-header">
            <div class="agent-info">
                <div class="agent-avatar">🤖</div>
                <div class="agent-status-container">
                    <span class="agent-name">Agente Alura</span>
                    <span class="agent-status"><span class="status-dot"></span>Mentor en línea</span>
                </div>
            </div>
        </div>

        <div class="chat-messages" id="messages-container">
            <div class="message message-agent">
                ¡Hola! Bienvenido a Neouniverse. Soy tu **Agente Alura**, tu mentor de onboarding. ¿En qué puedo ayudarte hoy respecto a nuestra arquitectura, guías de estilo o procesos?
            </div>
        </div>

        <div class="typing-indicator" id="indicator">
            <div class="dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        </div>

        <div class="chat-input-area">
            <input type="text" class="chat-input" id="user-input" placeholder="Escribe tu duda técnica aquí..." onkeydown="checkEnter(event)">
            <button class="send-btn" onclick="sendMessage()">Enviar</button>
        </div>
    </div>

    <script>
        const session_id = 'session_' + Math.random().toString(36).substr(2, 9);
        const container = document.getElementById('messages-container');
        const input = document.getElementById('user-input');
        const indicator = document.getElementById('indicator');

        function checkEnter(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        }

        async function sendMessage() {
            const query = input.value.trim();
            if (!query) return;

            // Mostrar mensaje del usuario
            appendMessage(query, 'user');
            input.value = '';
            
            // Mostrar indicador de carga
            indicator.style.display = 'block';
            container.scrollTop = container.scrollHeight;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ input: query, session_id: session_id })
                });
                
                const data = await response.json();
                indicator.style.display = 'none';

                if (data.error) {
                    appendMessage('⚠️ Error: ' + data.error, 'agent');
                } else {
                    appendMessage(data.response, 'agent');
                }
            } catch (err) {
                indicator.style.display = 'none';
                appendMessage('⚠️ Hubo un problema al conectar con el servidor.', 'agent');
            }
        }

        function appendMessage(text, sender) {
            const msgDiv = document.createElement('div');
            msgDiv.classList.add('message', sender === 'user' ? 'message-user' : 'message-agent');
            
            if (sender === 'agent') {
                // Formateador markdown básico y rápido para la web
                msgDiv.innerHTML = formatMarkdown(text);
            } else {
                msgDiv.textContent = text;
            }
            
            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
        }

        function formatMarkdown(text) {
            let formatted = text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/\\n/g, '<br>')
                .replace(/\n/g, '<br>')
                // Formatear bloques de código
                .replace(/```(.*?)\s+([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
                // Formatear código en línea
                .replace(/`(.*?)`/g, '<code>$1</code>')
                // Negritas
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                // Listas
                .replace(/^\s*-\s+(.*?)(?:<br>|$)/gm, '<li>$1</li>')
                .replace(/(<li>.*?<\/li>)/s, '<ul>$1</ul>');

            return formatted;
        }
    </script>
</body>
</html>
"""

# Rutas de la Aplicación
@app.route("/")
def home():
    return render_template_string(HTML_CHAT)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json or {}
    pregunta = data.get("input", "").strip()
    session_id = data.get("session_id", "default_session")
    
    if not pregunta:
        return jsonify({"error": "Entrada vacía"}), 400

    try:
        chain, llm_with_tools = obtener_cadena_agente()
        
        # Obtener o crear historial de la sesión
        if session_id not in historiales_por_sesion:
            historiales_por_sesion[session_id] = InMemoryChatMessageHistory()
        
        historial = historiales_por_sesion[session_id]
        mensajes_previos = historial.messages
        
        # Invocar la primera parte
        respuesta = chain.invoke({
            "input": pregunta,
            "history": mensajes_previos
        })
        
        historial.add_user_message(pregunta)
        
        # Manejar llamadas a herramientas en bucle
        if respuesta.tool_calls:
            historial.add_message(respuesta)
            
            for tool_call in respuesta.tool_calls:
                nombre_tool = tool_call["name"]
                argumentos = tool_call["args"]
                tool_id = tool_call["id"]
                
                # Ejecutar herramientas
                resultado_tool = ""
                if nombre_tool == "buscar_en_internet":
                    resultado_tool = buscar_en_internet.invoke(argumentos)
                elif nombre_tool == "ejecutar_codigo_sandbox":
                    resultado_tool = ejecutar_codigo_sandbox.invoke(argumentos)
                
                tool_message = ToolMessage(
                    content=str(resultado_tool),
                    tool_call_id=tool_id,
                    name=nombre_tool
                )
                historial.add_message(tool_message)
            
            respuesta_final = llm_with_tools.invoke(historial.messages)
            historial.add_message(respuesta_final)
            texto_respuesta = respuesta_final.content
        else:
            historial.add_message(respuesta)
            texto_respuesta = respuesta.content
            
        return jsonify({"response": texto_respuesta})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    puerto = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=puerto)
