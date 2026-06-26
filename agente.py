import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Evitar errores de codificación raros al imprimir texto en consolas de Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# 1. Cargar la clave secreta de Gemini desde el archivo .env
load_dotenv()
clave_api = os.getenv("GEMINI_API_KEY")

if not clave_api:
    print("[ERROR] No se encontró la clave GEMINI_API_KEY en el archivo .env")
    print("Por favor, agrega tu clave en el archivo .env para poder continuar.")
    sys.exit(1)

# 2. Leer todos los documentos de la base de conocimientos
directorio_conocimientos = "base-conocimiento"
contexto_manuales = ""

print("Leyendo los archivos de la base de conocimiento...")

if os.path.exists(directorio_conocimientos):
    archivos = os.listdir(directorio_conocimientos)
    for nombre_archivo in archivos:
        ruta_completa = os.path.join(directorio_conocimientos, nombre_archivo)
        
        # Solo leemos archivos que sean de texto o markdown (.md, .csv, .txt)
        if os.path.isfile(ruta_completa) and nombre_archivo.endswith(('.md', '.csv', '.txt')):
            try:
                # Leer el contenido del archivo de forma simple
                with open(ruta_completa, "r", encoding="utf-8") as f:
                    contenido = f.read()
                
                # Adjuntarlo al gran bloque de contexto
                contexto_manuales += f"\n--- INICIO DE ARCHIVO: {nombre_archivo} ---\n"
                contexto_manuales += contenido
                contexto_manuales += f"\n--- FIN DE ARCHIVO: {nombre_archivo} ---\n"
                print(f"- Leído con éxito: {nombre_archivo}")
            except Exception as e:
                print(f"- Error al leer {nombre_archivo}: {e}")
else:
    print(f"[ADVERTENCIA] No existe la carpeta '{directorio_conocimientos}' en la raíz del proyecto.")

# 3. Prompt del sistema con instrucciones simplificadas
instrucciones_sistema = f"""Actúas como 'Agente Alura', un mentor técnico para la compañía Neouniverse.
Tu trabajo es responder preguntas de los colaboradores basándote estrictamente en los documentos corporativos provistos a continuación.

REGLAS SENCILLAS:
1. Responde de forma clara, directa, amigable y estructurada en Markdown.
2. Si la respuesta está en los documentos de abajo, úsalos para contestar directamente de forma natural, asumiendo el conocimiento como tuyo.
3. No muestres metadatos de archivos, ni secciones de "Referencias" o "Fuentes utilizadas". Queremos un mensaje limpio de chat.
4. Si la información solicitada no está en los manuales de abajo, di amablemente: "Lo siento, la información solicitada no se encuentra en la base de conocimientos de Neouniverse. Por favor, comunícate en el canal de Slack #soporte-arquitectura."

DOCUMENTOS DE NEOUNIVERSE:
{contexto_manuales}"""

# 4. Selector de Proveedor
print("\nSeleccione el proveedor de Inteligencia Artificial:")
print("1. Gemini (Google) [Por defecto]")
print("2. Nemotron (NVIDIA)")
seleccion = input("Selección (1 o 2): ").strip()

proveedor = "gemini"
clave_nvidia = None
modelo_nvidia = None
historial_nvidia = []
sesion_chat = None

if seleccion == "2":
    proveedor = "nvidia"
    clave_nvidia = os.getenv("NVIDIA_API_KEY")
    modelo_nvidia = os.getenv("NVIDIA_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct")
    if not clave_nvidia:
        print("[ERROR] No se encontró la clave NVIDIA_API_KEY en el archivo .env")
        sys.exit(1)
    # Inicializar historial para Nvidia
    historial_nvidia = [
        {"role": "system", "content": instrucciones_sistema}
    ]
    print(f"\nConectando con la API de NVIDIA (Modelo: {modelo_nvidia})...")
else:
    print("\nConectando con la inteligencia artificial de Gemini...")
    try:
        cliente_ai = genai.Client(api_key=clave_api)
        # Creamos un chat continuo en Gemini que recordará el historial de la conversación
        sesion_chat = cliente_ai.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=instrucciones_sistema
            )
        )
    except Exception as e:
        print(f"[ERROR] No se pudo inicializar la conexión con Gemini: {e}")
        sys.exit(1)

# 5. Iniciar la sesión de chat interactiva
print("\n==================================================================")
print(f"🤖 Agente Alura — Consola de Chat Interactiva ({'NVIDIA Nemotron' if proveedor == 'nvidia' else 'Gemini Google'}) 🤖")
print("==================================================================")
print("Escribe tus consultas sobre Neouniverse. Para salir escribe: salir\n")

# 6. Bucle infinito para chatear en la terminal
while True:
    try:
        pregunta = input("\nTú: ").strip()
        
        # Ignorar de forma segura entradas vacías
        if not pregunta:
            continue
            
        # Salir del bucle si el usuario escribe 'salir'
        if pregunta.lower() in ["salir", "exit", "quit"]:
            print("\n¡Hasta luego! Que tengas un excelente día de desarrollo.")
            break
            
        print("Agente Alura está pensando...")
        
        if proveedor == "gemini":
            # Enviar la pregunta al chat de Gemini
            respuesta = sesion_chat.send_message(pregunta)
            print(f"\nAgente Alura:\n{respuesta.text}")
        else:
            # Enviar la pregunta a Nvidia usando requests
            historial_nvidia.append({"role": "user", "content": pregunta})
            
            url = "https://integrate.api.nvidia.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {clave_nvidia}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": modelo_nvidia,
                "messages": historial_nvidia,
                "temperature": 0.5,
                "max_tokens": 1024
            }
            
            import requests
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                respuesta_json = response.json()
                texto_respuesta = respuesta_json["choices"][0]["message"]["content"]
                historial_nvidia.append({"role": "assistant", "content": texto_respuesta})
                print(f"\nAgente Alura:\n{texto_respuesta}")
            else:
                print(f"\n⚠️ Error al obtener respuesta de NVIDIA NIM: {response.status_code} - {response.text}")
                
        print("-" * 60)
        
    except KeyboardInterrupt:
        print("\n\n¡Hasta luego! Conversación terminada.")
        break
    except Exception as e:
        print(f"\n⚠️ Ocurrió un problema al obtener respuesta: {e}")
