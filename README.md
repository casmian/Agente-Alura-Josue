# Agente Alura: Mentor Técnico de Onboarding 🤖📚

**Agente Alura** es un asistente cognitivo inteligente interactivo diseñado para actuar como mentor técnico y resolver dudas de onboarding, guías de estilo de código, arquitectura de microservicios y políticas operativas de la compañía **Neouniverse** basándose en la documentación oficial.

Esta versión está estructurada como un script interactivo de consola (CLI) que implementa un agente conversacional reactivo con acceso a herramientas externas y recuperación de información local.

---

## 🏗️ Estructura del Programa (Arquitectura del Proyecto)

El programa se construye combinando capacidades de modelos de lenguaje, recuperación de información y ejecución de herramientas:

1. **Orquestación con LangChain**: Utiliza `langchain` y `langchain-google-genai` para interactuar de forma fluida con el modelo de lenguaje de Google (`gemini-2.5-flash`).
2. **Inyección de Contexto en Tiempo Real (RAG Local)**: Antes de iniciar, el script lee dinámicamente todos los archivos de texto (`.md`, `.csv`, `.txt`) del directorio `base-conocimiento/` y los inyecta en la instrucción de sistema como la base de datos de conocimiento oficial de Neouniverse.
3. **Historial de Mensajes**: Mantiene una memoria local en tiempo de ejecución (`InMemoryChatMessageHistory`) para que el agente recuerde el contexto de los mensajes previos durante el chat interactivo.
4. **Bucle de Ejecución Reactivo (ReAct)**: El agente puede decidir de manera autónoma si necesita invocar una herramienta externa para responder a la consulta del usuario, manejar la llamada y reincorporar el resultado al flujo de la conversación antes de dar una respuesta final.

---

## 🛠️ Herramientas Integradas (Tools)

El agente dispone de dos herramientas principales que invoca automáticamente cuando es necesario:

* **Buscar en Internet (`buscar_en_internet`)**: Utiliza la API de Wikipedia en español para buscar información técnica general de programación, APIs o conceptos de desarrollo de software si la respuesta no se encuentra en los manuales de la empresa.
* **Ejecutar Código Sandbox (`ejecutar_codigo_sandbox`)**: Permite ejecutar de manera segura pequeños fragmentos de código de Python en un entorno controlado dentro de la memoria del sistema. Se utiliza para validar las soluciones a los retos técnicos de los desarrolladores o comprobar sintaxis técnica de forma automática.

---

## 📁 Estructura del Repositorio

El proyecto consta de los siguientes componentes principales:

* **`base-conocimiento/`**: Directorio que contiene los manuales, guías y políticas de la compañía Neouniverse en formatos Markdown (`.md`) y CSV (`.csv`).
* **`agente.py`**: El script principal que inicializa el cliente del modelo, carga el contexto de conocimiento local, define las herramientas y corre el bucle de conversación interactivo en la terminal.
* **`requirements.txt`**: Archivo de dependencias requeridas (incluye `google-genai`, `python-dotenv`, `langchain` y `langchain-google-genai`).
* **`.env`**: Archivo de variables de entorno para almacenar de forma segura la API Key de Gemini (`GEMINI_API_KEY`).
* **`.gitignore`**: Configuración de Git para omitir recursos temporales del sistema, la caché local y archivos de configuración personal.

---

## 🚀 Configuración Local e Instalación

### 1. Requisitos Previos
* **Python 3.10 o superior** instalado en el sistema.

### 2. Configurar Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto y agrega tu API Key de Gemini:
```env
GEMINI_API_KEY=tu_clave_api_aqui
```

### 3. Instalación de Dependencias e Inicialización
Crea y activa un entorno virtual de Python, e instala las dependencias necesarias:

```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# En Windows (PowerShell):
.venv\Scripts\Activate.ps1
# En Linux/macOS:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

---

## 🏃 Cómo Ejecutar el Agente

Para iniciar la conversación interactiva en la terminal, ejecuta:

```bash
python agente.py
```

Escribe tus consultas directamente en el prompt interactivo. El agente evaluará si requiere de herramientas externas o del contexto local para responderte. Para finalizar la conversación, simplemente escribe **`salir`** y presiona Enter.

---

## ☁️ Evidencia de Despliegue en la Nube (PythonAnywhere)

Como comprobación de que el **Agente Alura** se encuentra activo y corriendo de forma interactiva en la nube, se documentan las siguientes evidencias:

1. **Instalación e Inicialización del Entorno**: Clonación del repositorio, instalación exitosa de los requerimientos y carga inicial del agente en la terminal de PythonAnywhere:
   * Ver captura: [Evidencia de Inicialización](./evidencias/inicializacion_nube.png)
2. **Prueba de Funcionamiento y Chat**: Conversación interactiva en tiempo real con el agente desde la consola web del navegador en la nube:
   * Ver captura: [Evidencia de Chat en la Nube](./evidencias/chat_nube.png)

