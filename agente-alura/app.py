import os
import sys
from dotenv import load_dotenv

# Evitar errores de codificación en consolas Windows (CP1252)
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Permitir importaciones relativas
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.orchestrator import run_agent_conversation

def run_cli_chat():
    load_dotenv()
    
    print("==================================================================")
    print("🤖 Agente Alura — Consola Interactiva (Python Puro) 🤖")
    print("==================================================================")
    print("Puedes hacer preguntas sobre onboarding, estilo, bases de datos,")
    print("arquitectura de Neouniverse o políticas corporativas.")
    print("Escribe 'salir' o 'exit' para terminar.\n")
    
    user_id = "desarrollador-cli"
    chat_id = None
    
    # Filtro opcional de categoría
    print("Categorías disponibles para filtrar:")
    print("1. Entorno (onboarding, incidentes, configuracion)")
    print("2. Estilo (buenas practicas frontend/backend)")
    print("3. Arquitectura (esquema vectorial, bases de datos)")
    print("4. Ninguno (Buscar en toda la base de conocimientos)\n")
    
    opcion = input("Selecciona una categoría (1-4) [Por defecto: 4]: ").strip()
    
    category_filter = None
    if opcion == "1":
        category_filter = "Entorno"
    elif opcion == "2":
        category_filter = "Estilo"
    elif opcion == "3":
        category_filter = "Arquitectura"
        
    if category_filter:
        print(f"[Filtro Activo]: Buscando únicamente en la categoría '{category_filter}'\n")
    else:
        print("[Filtro Inactivo]: Buscando en toda la base de conocimientos\n")
        
    while True:
        try:
            message = input("\nTú: ").strip()
            if not message:
                continue
                
            if message.lower() in ["salir", "exit", "quit"]:
                print("\n¡Hasta luego! Que tengas un excelente día de desarrollo.")
                break
                
            print("Pensando...")
            # Ejecutar la conversación RAG y obtener respuesta
            result = run_agent_conversation(
                user_id=user_id,
                message=message,
                chat_id=chat_id,
                category_filter=category_filter
            )
            
            # Guardar el ID de chat para mantener el historial del hilo
            chat_id = result["chatId"]
            
            print(f"\nAgente Alura:\n{result['reply']}")
            print("-" * 66)
            
        except KeyboardInterrupt:
            print("\n\n¡Hasta luego! Conversación terminada.")
            break
        except Exception as e:
            print(f"\n⚠️ Ocurrió un error: {e}")

if __name__ == "__main__":
    run_cli_chat()
