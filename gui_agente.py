import os
import sys
import threading
import queue
import re
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, scrolledtext
from dotenv import load_dotenv
from google import genai
from google.genai import types

# -------------------------------------------------------------
# CONFIGURACIÓN DE COLORES (Catppuccin Mocha Inspired)
# -------------------------------------------------------------
FONDO_PRINCIPAL = "#1e1e2e"          # Fondo principal oscuro
FONDO_CHAT = "#181825"          # Fondo del área de chat
FONDO_MARCO_ENTRADA = "#11111b"   # Fondo de la barra de entrada inferior
TEXTO_PRINCIPAL = "#cdd6f4"          # Texto general (blanco suave)
TEXTO_MUTADO = "#7f849c"         # Texto secundario/deshabilitado
ACENTO_AZUL = "#89b4fa"      # Acento azul para botones y títulos
ACENTO_VERDE = "#a6e3a1"     # Acento verde para el Agente
ACENTO_ROSA = "#f5c2e7"      # Acento rosa para el Usuario
ACENTO_MALVA = "#cba6f7"     # Acento violeta para sistema
COLOR_ERROR = "#f38ba8"      # Rojo para errores
FONDO_CODIGO = "#313244"          # Fondo para bloques de código
TEXTO_CODIGO = "#f5e0dc"          # Texto para bloques de código

FAMILIA_FUENTE = "Segoe UI" if sys.platform.startswith("win") else "Helvetica"
TAMANO_FUENTE = 10

class InterfazAgenteAlura:
    def __init__(self, raiz):
        self.raiz = raiz
        self.raiz.title("Agente Alura — Mentor de Onboarding")
        self.raiz.geometry("680x750")
        self.raiz.configure(bg=FONDO_PRINCIPAL)
        self.raiz.minsize(500, 600)
        
        # Cola para comunicación entre el hilo de la API y la interfaz gráfica
        self.cola_respuestas = queue.Queue()
        
        # Variables de estado
        self.sesion_chat = None
        self.cargando = False
        
        # Construir Interfaz Gráfica
        self.crear_widgets()
        
        # Iniciar la inicialización en segundo plano (para no congelar la interfaz al arrancar)
        self.mostrar_mensaje_sistema("Cargando la base de conocimientos y configurando la IA de Gemini...")
        threading.Thread(target=self.inicializar_agente, daemon=True).start()
        
        # Iniciar chequeo periódico de la cola de respuestas
        self.chequear_cola_respuestas()

    def crear_widgets(self):
        # 1. BÁNER SUPERIOR
        self.marco_cabecera = tk.Frame(self.raiz, bg=FONDO_PRINCIPAL, pady=15)
        self.marco_cabecera.pack(fill=tk.X, padx=20)
        
        self.etiqueta_titulo = tk.Label(
            self.marco_cabecera, 
            text="🤖 Agente Alura", 
            font=(FAMILIA_FUENTE, 16, "bold"), 
            bg=FONDO_PRINCIPAL, 
            fg=ACENTO_AZUL
        )
        self.etiqueta_titulo.pack(anchor="w")
        
        self.etiqueta_subtitulo = tk.Label(
            self.marco_cabecera, 
            text="Mentor Técnico de Onboarding — Neouniverse", 
            font=(FAMILIA_FUENTE, 9, "italic"), 
            bg=FONDO_PRINCIPAL, 
            fg=TEXTO_MUTADO
        )
        self.etiqueta_subtitulo.pack(anchor="w")

        # 2. ÁREA DE CHAT (CENTRAL)
        self.marco_chat = tk.Frame(self.raiz, bg=FONDO_PRINCIPAL)
        self.marco_chat.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        self.registro_chat = scrolledtext.ScrolledText(
            self.marco_chat, 
            wrap=tk.WORD, 
            bg=FONDO_CHAT, 
            fg=TEXTO_PRINCIPAL, 
            insertbackground=TEXTO_PRINCIPAL,
            font=(FAMILIA_FUENTE, TAMANO_FUENTE),
            bd=0, 
            highlightthickness=1,
            highlightbackground="#313244",
            highlightcolor=ACENTO_AZUL,
            padx=10,
            pady=10
        )
        self.registro_chat.pack(fill=tk.BOTH, expand=True)
        
        # Configurar etiquetas de estilo para el texto de chat
        self.registro_chat.tag_config("user_header", font=(FAMILIA_FUENTE, 10, "bold"), foreground=ACENTO_ROSA)
        self.registro_chat.tag_config("agent_header", font=(FAMILIA_FUENTE, 10, "bold"), foreground=ACENTO_VERDE)
        self.registro_chat.tag_config("system", font=(FAMILIA_FUENTE, 9, "italic"), foreground=ACENTO_MALVA)
        self.registro_chat.tag_config("error", font=(FAMILIA_FUENTE, 10, "bold"), foreground=COLOR_ERROR)
        self.registro_chat.tag_config("timestamp", font=(FAMILIA_FUENTE, 8), foreground=TEXTO_MUTADO)
        self.registro_chat.tag_config("bold", font=(FAMILIA_FUENTE, TAMANO_FUENTE, "bold"))
        self.registro_chat.tag_config("code", font=("Courier New", TAMANO_FUENTE), background=FONDO_CODIGO, foreground=TEXTO_CODIGO)
        
        # Hacer que el registro_chat sea de solo lectura para el usuario
        self.registro_chat.config(state=tk.DISABLED)

        # 3. BARRA DE ENTRADA INFERIOR
        self.marco_entrada = tk.Frame(self.raiz, bg=FONDO_MARCO_ENTRADA, pady=12)
        self.marco_entrada.pack(fill=tk.X, ipady=5)
        
        self.entrada_mensaje = tk.Entry(
            self.marco_entrada, 
            bg="#313244", 
            fg=TEXTO_PRINCIPAL, 
            insertbackground=TEXTO_PRINCIPAL,
            font=(FAMILIA_FUENTE, TAMANO_FUENTE),
            bd=0, 
            highlightthickness=1,
            highlightbackground="#45475a",
            highlightcolor=ACENTO_AZUL
        )
        self.entrada_mensaje.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15, 10), ipady=8)
        self.entrada_mensaje.bind("<Return>", lambda evento: self.enviar_mensaje())
        self.entrada_mensaje.config(state=tk.DISABLED) # Deshabilitado hasta que cargue la IA

        self.boton_enviar = tk.Button(
            self.marco_entrada, 
            text="Enviar", 
            font=(FAMILIA_FUENTE, 9, "bold"),
            bg=ACENTO_AZUL, 
            fg=FONDO_MARCO_ENTRADA,
            activebackground="#b4befe",
            activeforeground=FONDO_MARCO_ENTRADA,
            bd=0, 
            padx=15, 
            command=self.enviar_mensaje
        )
        self.boton_enviar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 15))
        self.boton_enviar.config(state=tk.DISABLED)

        # 4. BARRA DE ESTADO (PIE DE PÁGINA)
        self.barra_estado = tk.Label(
            self.raiz, 
            text="Inicializando...", 
            bd=0, 
            anchor="w", 
            bg=FONDO_PRINCIPAL, 
            fg=TEXTO_MUTADO,
            font=(FAMILIA_FUENTE, 8),
            padx=20,
            pady=5
        )
        self.barra_estado.pack(fill=tk.X)

    # -------------------------------------------------------------
    # LÓGICA DE INICIALIZACIÓN
    # -------------------------------------------------------------
    def inicializar_agente(self):
        load_dotenv()
        clave_api = os.getenv("GEMINI_API_KEY")
        
        if not clave_api:
            self.cola_respuestas.put(("INIT_ERROR", "No se encontró la clave GEMINI_API_KEY en el archivo .env.\nPor favor agrégala para poder interactuar con el agente."))
            return
 
        directorio_conocimientos = "base-conocimiento"
        contexto_manuales = ""
        
        # Leer base de conocimientos
        if os.path.exists(directorio_conocimientos):
            try:
                archivos = os.listdir(directorio_conocimientos)
                for nombre_archivo in archivos:
                    ruta_completa = os.path.join(directorio_conocimientos, nombre_archivo)
                    if os.path.isfile(ruta_completa) and nombre_archivo.endswith(('.md', '.csv', '.txt')):
                        with open(ruta_completa, "r", encoding="utf-8") as f:
                            contenido = f.read()
                        contexto_manuales += f"\n--- INICIO DE ARCHIVO: {nombre_archivo} ---\n"
                        contexto_manuales += contenido
                        contexto_manuales += f"\n--- FIN DE ARCHIVO: {nombre_archivo} ---\n"
            except Exception as e:
                self.cola_respuestas.put(("INIT_ERROR", f"Error leyendo base de conocimientos: {e}"))
                return
        else:
            self.cola_respuestas.put(("WARNING", f"No se encontró la carpeta '{directorio_conocimientos}'. El agente no tendrá contexto corporativo."))
 
        # Configurar instrucciones del sistema
        instrucciones_sistema = f"""Actúas como 'Agente Alura', un mentor técnico para la compañía Neouniverse.
Tu trabajo es responder preguntas de los colaboradores basándote estrictamente en los documentos corporativos provistos a continuación.

REGLAS SENCILLAS:
1. Responde de forma clara, directa, amigable y estructurada en Markdown.
2. Si la respuesta está en los documentos de abajo, úsalos para contestar directamente de forma natural, asumiendo el conocimiento como tuyo.
3. No muestres metadatos de archivos, ni secciones de "Referencias" o "Fuentes utilizadas". Queremos un mensaje limpio de chat.
4. Si la información solicitada no está en los manuales de abajo, di amablemente: "Lo siento, la información solicitada no se encuentra en la base de conocimientos de Neouniverse. Por favor, comunícate en el canal de Slack #soporte-arquitectura."

DOCUMENTOS DE NEOUNIVERSE:
{contexto_manuales}"""
 
        # Inicializar API
        try:
            self.cliente_ai = genai.Client(api_key=clave_api)
            self.sesion_chat = self.cliente_ai.chats.create(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction=instrucciones_sistema
                )
            )
            self.cola_respuestas.put(("INIT_SUCCESS", "¡Conectado exitosamente con Gemini!"))
        except Exception as e:
            self.cola_respuestas.put(("INIT_ERROR", f"No se pudo conectar con Gemini: {e}"))

    # -------------------------------------------------------------
    # MÉTODOS DE ACTUALIZACIÓN DE UI
    # -------------------------------------------------------------
    def mostrar_mensaje_sistema(self, mensaje):
        self.registro_chat.config(state=tk.NORMAL)
        self.registro_chat.insert(tk.END, f"⚙️ {mensaje}\n\n", "system")
        self.registro_chat.config(state=tk.DISABLED)
        self.registro_chat.see(tk.END)

    def mostrar_mensaje_error(self, mensaje):
        self.registro_chat.config(state=tk.NORMAL)
        self.registro_chat.insert(tk.END, f"⚠️ Error: {mensaje}\n\n", "error")
        self.registro_chat.config(state=tk.DISABLED)
        self.registro_chat.see(tk.END)

    def establecer_estado(self, texto):
        self.barra_estado.config(text=texto)

    # -------------------------------------------------------------
    # FORMATEO DE MENSAJES Y RENDERING DE MARKDOWN BÁSICO
    # -------------------------------------------------------------
    def insertar_mensaje_formateado(self, remitente, texto):
        self.registro_chat.config(state=tk.NORMAL)
        
        # Insertar cabecera con el remitente y la hora
        ahora = datetime.now().strftime("%H:%M")
        tag_cabecera = "user_header" if remitente == "Tú" else "agent_header"
        
        self.registro_chat.insert(tk.END, f"{remitente} ", tag_cabecera)
        self.registro_chat.insert(tk.END, f"[{ahora}]\n", "timestamp")
        
        # Procesar Markdown básico (**negrita** y `código`)
        # Separar bloques por negrita o bloques de código para aplicar etiquetas correspondientes
        partes = re.split(r'(\*\*.*?\*\*|`.*?`)', texto)
        for parte in partes:
            if parte.startswith('**') and parte.endswith('**'):
                # Eliminar las estrellas e insertar como negrita
                contenido = parte[2:-2]
                self.registro_chat.insert(tk.END, contenido, "bold")
            elif parte.startswith('`') and parte.endswith('`'):
                # Eliminar las comillas invertidas e insertar como código
                contenido = parte[1:-1]
                self.registro_chat.insert(tk.END, contenido, "code")
            else:
                self.registro_chat.insert(tk.END, parte)
                
        self.registro_chat.insert(tk.END, "\n\n")
        self.registro_chat.config(state=tk.DISABLED)
        self.registro_chat.see(tk.END)

    # -------------------------------------------------------------
    # LÓGICA DE ENVÍO DE MENSAJES Y ASINCRONÍA
    # -------------------------------------------------------------
    def enviar_mensaje(self):
        if self.cargando or not self.sesion_chat:
            return
            
        mensaje = self.entrada_mensaje.get().strip()
        if not mensaje:
            return
            
        # Limpiar entrada y mostrar el mensaje del usuario
        self.entrada_mensaje.delete(0, tk.END)
        self.insertar_mensaje_formateado("Tú", mensaje)
        
        # Deshabilitar controles mientras piensa
        self.cargando = True
        self.entrada_mensaje.config(state=tk.DISABLED)
        self.boton_enviar.config(state=tk.DISABLED)
        self.establecer_estado("Agente Alura está pensando...")
        
        # Crear hilo para consultar a Gemini sin congelar la interfaz
        threading.Thread(target=self.hilo_consultar_gemini, args=(mensaje,), daemon=True).start()

    def hilo_consultar_gemini(self, mensaje):
        try:
            respuesta = self.sesion_chat.send_message(mensaje)
            self.cola_respuestas.put(("CHAT_SUCCESS", respuesta.text))
        except Exception as e:
            self.cola_respuestas.put(("CHAT_ERROR", str(e)))

    def chequear_cola_respuestas(self):
        try:
            while True:
                tipo, datos = self.cola_respuestas.get_nowait()
                
                if tipo == "INIT_SUCCESS":
                    self.mostrar_mensaje_sistema(datos)
                    self.establecer_estado("Conectado. Escribe una pregunta.")
                    self.entrada_mensaje.config(state=tk.NORMAL)
                    self.boton_enviar.config(state=tk.NORMAL)
                    self.entrada_mensaje.focus_set()
                    
                elif tipo == "INIT_ERROR":
                    self.mostrar_mensaje_error(datos)
                    self.establecer_estado("Error de inicialización.")
                    messagebox.showerror("Error de Configuración", datos)
                    
                elif tipo == "WARNING":
                    self.mostrar_mensaje_sistema(f"Advertencia: {datos}")
                    
                elif tipo == "CHAT_SUCCESS":
                    self.insertar_mensaje_formateado("Agente Alura", datos)
                    self.establecer_estado("Conectado")
                    self.cargando = False
                    self.entrada_mensaje.config(state=tk.NORMAL)
                    self.boton_enviar.config(state=tk.NORMAL)
                    self.entrada_mensaje.focus_set()
                    
                elif tipo == "CHAT_ERROR":
                    self.mostrar_mensaje_error(f"Error en respuesta: {datos}")
                    self.establecer_estado("Error al obtener respuesta")
                    self.cargando = False
                    self.entrada_mensaje.config(state=tk.NORMAL)
                    self.boton_enviar.config(state=tk.NORMAL)
                    self.entrada_mensaje.focus_set()
                    
                self.cola_respuestas.task_done()
        except queue.Empty:
            pass
            
        # Re-programar el chequeo cada 100 ms
        self.raiz.after(100, self.chequear_cola_respuestas)

# -------------------------------------------------------------
# EJECUCIÓN PRINCIPAL
# -------------------------------------------------------------
if __name__ == "__main__":
    # Asegurar codificación utf-8 en Windows para stdout
    if sys.platform.startswith('win'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    raiz = tk.Tk()
    aplicacion = InterfazAgenteAlura(raiz)
    raiz.mainloop()
