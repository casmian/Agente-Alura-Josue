# Reglas de Desarrollo para el Agente Alura

Este archivo define las reglas de comportamiento y la pila tecnológica que guiarán el desarrollo del proyecto **Agente Alura**. Todas las implementaciones de código, arquitectura y documentación deben alinearse con estas directrices.

## 🛠️ Pila Tecnológica Recomendada

El proyecto del Agente Alura se construirá utilizando las siguientes tecnologías:

1. **Frontend**:
   - **Framework**: React + Vite (con TypeScript) para una interfaz SPA rápida y modular.
   - **Estilado**: Vanilla CSS personalizado (variables CSS, animaciones interactivas, layouts responsivos, diseño de modo oscuro y micro-animaciones premium). Se debe evitar TailwindCSS para mantener un control absoluto sobre el diseño visual.
2. **Backend**:
   - **Entorno**: Node.js con TypeScript (Express o Fastify) para la orquestación y el servidor del agente.
3. **AI / LLM Integration**:
   - **SDK**: Google Gen AI SDK (`@google/genai`) para la conexión nativa con modelos Gemini (como Gemini 1.5 Pro/Flash o Gemini 2.0).
4. **Almacenamiento y RAG**:
   - **Base de Datos**: PostgreSQL con la extensión `pgvector` para almacenamiento de perfiles de usuario, historial de conversación y búsqueda semántica de cursos de Alura.

---

## 🤖 Capacidades del Agente Alura

El agente desarrollado debe cumplir con las siguientes funciones clave:

1. **Tutor de Programación Interactivo**: Explicar conceptos técnicos enseñados en Alura, proponer retos de código personalizados y evaluar las soluciones de los alumnos de manera constructiva.
2. **Recomendador de Rutas**: Analizar el perfil y progreso del alumno en Alura para aconsejar los siguientes cursos más adecuados.
3. **Compañero de Consultas (RAG)**: Responder preguntas sobre cursos y plataforma mediante la recuperación de información desde transcripciones de clases y documentación de Alura.
4. **Sandbox / Ejecución de Herramientas**: Integración con herramientas seguras para buscar en internet (Google Search) o validar pequeñas estructuras de código mediante Function Calling de Gemini.
