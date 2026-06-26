# Agente Alura: Mentor Técnico de Onboarding 🤖📚

**Agente Alura** es un asistente cognitivo inteligente interactivo diseñado para actuar como mentor técnico y resolver dudas de onboarding, guías de estilo de código, arquitectura de microservicios y políticas operativas de la compañía **Neouniverse** basándose en la documentación oficial.

Esta actualización introduce una nueva **Interfaz Gráfica de Escritorio (GUI)** construida con Tkinter, además de la versión clásica de consola (CLI), ambas completamente adaptadas al español.

---

## 🏗️ Cómo está Construido (Arquitectura del Proyecto)

Para mantener la base de código simple, legible y fácil de mantener (apta para programadores de todos los niveles), el proyecto ha sido estructurado de la siguiente forma:

1. **Sin Base de Datos**: Se eliminó la necesidad de configurar servidores de bases de datos relacionales o complejas ingestas de embeddings vectoriales.
2. **Inyección de Contexto en Tiempo Real**: El script lee directamente los archivos de texto y markdown locales del directorio `base-conocimiento/` y los adjunta como parte de la instrucción de sistema (*system instruction*) a la API de Gemini, aprovechando la amplia ventana de contexto del modelo.
3. **Chat Interactivo Continuo**: Mantiene un hilo de conversación de memoria interactiva nativa gracias al objeto `chats` del SDK oficial de Google Gen AI.
4. **Hilos Asíncronos (para GUI)**: La interfaz gráfica ejecuta las llamadas a la API en un hilo secundario de ejecución (`threading`), evitando que la ventana se congele durante la generación de respuestas.
5. **Estilo Premium**: La interfaz gráfica cuenta con un esquema de colores oscuros inspirado en la paleta *Catppuccin Mocha*, ofreciendo un diseño elegante, moderno y limpio.

---

## 📁 Estructura del Repositorio

El proyecto consta de la siguiente estructura:

* **`base-conocimiento/`**: Carpeta que contiene todos los manuales y políticas de Neouniverse en formatos Markdown (`.md`) y CSV (`.csv`):
  * `Politicas_Corporativas_de_Seguridad_y_Operaciones__Neouniverse.md`
  * `Guia_de_Configuracion_y_Despliegue_Continuo_CICD__Neouniverse.md`
  * `Manual_de_Practicas_de_Pruebas_y_Calidad_de_Software_QA__Neouniverse.md`
  * `Guia_de_Monitoreo_y_Configuracion_de_Observabilidad__Neouniverse.md`
  * `Manual_de_Politicas_y_Procesos_de_RRHH__Neouniverse.md`
  * `Manual_de_Base_de_Datos_y_Esquema_Vectorial__Neouniverse.md`
  * `Manual_de_Onboarding_Nuevos_Desarrolladores__Neouniverse.md`
  * `Guia_Oficial_de_Ingenieria_Backend__Neouniverse.md`
  * `Guia_Oficial_de_Ingenieria_Frontend__Neouniverse.md`
  * `Arquitectura_de_Microservicios_y_Mapa_de_Dominios__Neouniverse.csv`
  * `Protocolo_de_Respuesta_a_Incidentes__Neouniverse.md`
* **`gui_agente.py`**: Interfaz gráfica de escritorio (GUI) en español construida con Tkinter/ttk que permite chatear en una ventana interactiva moderna.
* **`agente.py`**: Script clásico de consola (CLI) que inicia la conversación directamente en la terminal.
* **`requirements.txt`**: Archivo de dependencias mínimas requeridas (`google-genai` y `python-dotenv`).
* **`.env`**: Archivo local de variables de entorno para almacenar de forma segura la API Key de Gemini (`GEMINI_API_KEY`).
* **`.gitignore`**: Configuración de Git para omitir recursos temporales del sistema, la caché local y archivos de configuración personal.

---

## 🛠️ Configuración Local e Instalación

### 1. Requisitos Previos
* **Python 3.10 o superior** instalado en el sistema.

### 2. Variables de Entorno
Crea o edita el archivo `.env` en la raíz del proyecto y agrega tu API Key de Gemini:
```env
GEMINI_API_KEY=tu_clave_api_aqui
```

### 3. Instalación de Dependencias
Crea y activa un entorno virtual de Python, e instala las dependencias necesarias:
```bash
# Crear entorno virtual (opcional pero recomendado)
python -m venv .venv

# Activar entorno virtual
# En Windows (PowerShell):
.venv\Scripts\Activate.ps1
# En Linux/macOS:
source .venv/bin/activate

# Instalar requerimientos
pip install -r requirements.txt
```

---

## 🏃 Cómo Ejecutar el Agente

Puedes interactuar con el Agente Alura en cualquiera de sus dos modalidades:

### Opción A: Interfaz Gráfica (Recomendado) 🖥️
Inicia la ventana interactiva ejecutando el siguiente comando:
```bash
python gui_agente.py
```
Esta versión ofrece una ventana moderna con colores oscuros, scrolling automático, indicador visual de carga ("Pensando...") y formato para bloques de código y textos en negrita.

### Opción B: Consola de Comandos 💻
Si prefieres interactuar directamente desde la terminal clásica:
```bash
python agente.py
```
Escribe tus consultas directamente en el prompt. Para finalizar la conversación, simplemente escribe **`salir`** y presiona Enter.
