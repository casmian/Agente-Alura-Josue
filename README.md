# Agente Alura: Mentor Técnico de Onboarding (Python Simplificado) 🤖📚

**Agente Alura** es un asistente cognitivo inteligente interactivo diseñado para ejecutarse directamente en la terminal de comandos (CLI) utilizando Python puro. Su objetivo es actuar como un mentor técnico para resolver dudas de onboarding, guías de estilos de código, arquitectura de microservicios y políticas operativas de la compañía **Neouniverse** basándose en la documentación oficial de forma directa y sin sobreingeniería.

---

## 🏗️ Cómo está Construido (Arquitectura Simplificada)

Para mantener la base de código simple, legible y fácil de mantener (apta para programadores principiantes), el proyecto ha sido simplificado al máximo:

1. **Sin Base de Datos**: Se eliminó la necesidad de configurar servidores de base de datos relacionales, extensiones complejas como `pgvector` o ingestas de embeddings locales.
2. **Inyección de Contexto en Tiempo Real**: El script lee directamente los archivos de texto y markdown locales y los adjunta como parte del prompt del sistema (*system instruction*) a la API de Gemini, aprovechando la amplia ventana de contexto del modelo para una atención perfecta y precisa.
3. **Chat Interactivo Continuo**: Mantiene un hilo de conversación de memoria interactiva nativa gracias al objeto `chats` del SDK oficial de Google Gen AI.

---

## 📁 Estructura del Repositorio

El proyecto consta de una estructura minimalista de archivos:

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
* **`agente.py`**: Script monolítico principal de Python que lee el contexto e inicia la conversación en terminal.
* **`requirements.txt`**: Archivo de requerimientos de Python que contiene únicamente las dependencias básicas necesarias (`google-genai` y `python-dotenv`).
* **`.env`**: Archivo local de variables de entorno que almacena tu clave de API (`GEMINI_API_KEY`).
* **`.gitignore`**: Configuración de Git para omitir recursos temporales del sistema y la caché local.

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
Crea y activa un entorno virtual de Python, e instala las dependencias simplificadas:
```bash
# Crear entorno virtual (opcional)
python -m venv .venv

# Activar entorno virtual
# En Windows (PowerShell):
.venv\Scripts\Activate.ps1
# En Linux/macOS:
source .venv/bin/activate

# Instalar los requerimientos mínimos
pip install -r requirements.txt
```

---

## 🏃 Cómo Ejecutar el Agente

Una vez configurado el entorno, puedes chatear interactivamente con el agente de Neouniverse corriendo el script principal en tu terminal:

```bash
python agente.py
```

Escribe tus dudas técnicas u operativas en el prompt y el agente te responderá de forma directa. Para terminar la conversación, simplemente escribe **`salir`** y presiona Enter.
