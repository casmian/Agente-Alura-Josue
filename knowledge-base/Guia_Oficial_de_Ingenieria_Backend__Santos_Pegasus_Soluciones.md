# Guía Oficial de Ingeniería Back-end — Santos Pegasus Soluciones 📖💻

Este documento establece las directrices oficiales de codificación, las arquitecturas recomendadas y los estándares de diseño para el desarrollo backend en **Santos Pegasus Soluciones**.

---

## 🏗️ 1. Patrones de Arquitectura del Software

El backend y la lógica de inteligencia artificial se estructuran bajo una arquitectura limpia en capas (Layered Architecture), promoviendo la separación de conceptos (Separation of Concerns):

```
┌─────────────────────────────────────────────────────────┐
│              Capa de Rutas (Express Router)             │
│   Recibe la petición HTTP, maneja autenticación/cors    │
└────────────────────────────┬────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────┐
│          Capa de Controladores (Controllers)            │
│   Valida la entrada, orquesta servicios y responde      │
└────────────────────────────┬────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────┐
│        Capa de Servicios de Negocio (Services)          │
│   Lógica del negocio, manipulación de datos principales  │
└──────────────┬─────────────────────────────┬────────────┘
               ▼                             ▼
┌──────────────────────────────┐ ┌────────────────────────┐
│     Orquestador del Agente   │ │       Motor RAG        │
│   Historial de chat, Gemini  │ │   Búsqueda vectorial   │
│   API y Function Calling     │ │      en PostgreSQL     │
└──────────────────────────────┘ └────────────────────────┘
```

1. **Controladores (`/controllers`)**: Validan los parámetros recibidos por el cliente y envían el resultado estructurado. No contienen lógica de base de datos directa.
2. **Servicios (`/services`)**: Contienen las reglas de negocio globales y coordinan el acceso a bases de datos y APIs externas.
3. **Módulo del Agente (`/agent/orchestrator.ts`)**: Encargado exclusivo de configurar los prompts del sistema, mantener la memoria conversacional e interactuar con el SDK de Gemini.
4. **Motor RAG (`/agent/retrievalEngine.ts`)**: Clase dedicada a vectorizar las dudas de los usuarios y realizar búsquedas de similitud en la base de datos de embeddings.

---

## 💻 2. Estándar de TypeScript y Formateo
* **Tipado Estricto**: Habilita `"strict": true` en tu `tsconfig.json`. Queda prohibido el uso de `any`. Si un tipo no es conocido de antemano, usa `unknown` y realiza un estrechamiento de tipo (*type narrowing*).
* **Tipado de Retorno**: Todas las funciones exportadas y públicas deben declarar explícitamente su tipo de retorno.
* **Manejo de Errores Silencioso Prohibido**: Todo bloque `catch` debe manejar el error utilizando un sistema de registro centralizado (Winston logger) o propagarlo a través de un Middleware de errores global.

---

## 🔒 3. Conexión de Base de Datos y pgvector en OCI

Las consultas vectoriales a PostgreSQL deben realizarse optimizando la distancia de coseno (`<=>`) y utilizando los índices HNSW. A continuación se expone la estructura de un cliente SQL robusto:

```typescript
import { Pool } from 'pg';
import * as dotenv from 'dotenv';

dotenv.config();

const connectionString = process.env.DATABASE_URL;

export const dbPool = new Pool({
  connectionString,
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

export async function dbQuery(text: string, params?: any[]) {
  const start = Date.now();
  const res = await dbPool.query(text, params);
  const duration = Date.now() - start;
  console.log(`[SQL Query] Ejecutada en ${duration}ms | Filas devueltas: ${res.rowCount}`);
  return res;
}
```

### Consulta de Búsqueda Semántica Vectorial (RAG):
```sql
SELECT id, documento_nombre, categoria, contenido, ubicacion_exacta, autor_responsable,
       (embedding <=> $1) AS similitud
FROM document_chunks
WHERE categoria = $2 OR $2 IS NULL
ORDER BY embedding <=> $1
LIMIT $3;
```
*Nota: La métrica `<=>` representa la distancia de coseno. Cuanto menor sea el valor, mayor es la similitud semántica.*
