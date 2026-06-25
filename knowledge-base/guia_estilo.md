# Guía de Estilo de Código y Patrones de Arquitectura (Estándar Corporativo) 📖✨

Este documento establece las directrices de codificación, las arquitecturas recomendadas y los estándares de diseño para el **Agente Alura**. Cumplir con estas pautas garantiza la consistencia del código, facilita las pruebas automatizadas y mantiene una interfaz de usuario premium.

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
4. **Motor RAG (`/agent/rag.ts`)**: Clase dedicada a vectorizar las dudas de los alumnos y realizar búsquedas de similitud en la base de datos de embeddings.

---

## 💻 2. Estándar de TypeScript y Formateo

* **Tipado Estricto**: Habilita `"strict": true` en tu `tsconfig.json`. Queda prohibido el uso de `any`. Si un tipo no es conocido de antemano, usa `unknown` y realiza un estrechamiento de tipo (*type narrowing*).
* **Tipado de Retorno**: Todas las funciones exportadas y públicas deben declarar explícitamente su tipo de retorno.
* **Manejo de Errores Silencioso Prohibido**: Todo bloque `catch` debe manejar el error utilizando un sistema de registro centralizado (Winston logger) o propagarlo a través de un Middleware de errores global.

---

## 🎨 3. Estructura de Estilos CSS (Vanilla CSS Token System)

Para mantener la excelencia visual e interactiva sin frameworks externos, se utiliza un sistema de diseño basado en variables personalizadas de CSS (`CSS Custom Properties`) definidas en [**`index.css`**](file:///c:/Users/NeoUniverse/Agente-Alura/src/index.css):

```css
:root {
  /* Paleta de Colores (Diseño Modo Oscuro Premium) */
  --bg-primary: #0a0c10;
  --bg-secondary: #141722;
  --bg-glass: rgba(20, 23, 34, 0.7);
  --accent-color: #0c4cf5;
  --accent-glow: rgba(12, 76, 245, 0.4);
  --text-main: #f0f4f9;
  --text-muted: #8b9bb4;
  --border-color: rgba(139, 155, 180, 0.15);
  
  /* Fuentes y Tipografía */
  --font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
  
  /* Animaciones y Transiciones */
  --transition-smooth: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  --border-radius-m: 12px;
  --border-radius-l: 20px;
}
```

### Reglas de Diseño de la Interfaz:
- **Efecto Glassmorphism**: Utiliza `backdrop-filter: blur(10px)` con fondos semi-transparentes y bordes muy finos para las tarjetas y la ventana del chat.
- **Micro-animaciones**: Todos los botones interactivos deben tener un efecto hover suave. Ejemplo:
  ```css
  .btn-primary {
    transition: var(--transition-smooth);
  }
  .btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px var(--accent-glow);
  }
  ```

---

## 📝 4. Plantillas de Código de Producción

### A. Controlador de Backend (TypeScript + Express)
*Ubicación sugerida: `server/controllers/chatController.ts`*

```typescript
import { Request, Response, NextFunction } from 'express';
import { winstonLogger } from '../utils/logger';
import { runAgentConversation } from '../services/agentService';

interface ChatRequest {
  message: string;
  chatId?: string;
  userId: string;
}

/**
 * Procesa la consulta del estudiante enviando la información al Agente Alura
 */
export async function handleChatMessage(
  req: Request<{}, {}, ChatRequest>,
  res: Response,
  next: NextFunction
): Promise<void> {
  const { message, chatId, userId } = req.body;

  // 1. Validación de Entrada Estricta
  if (!message || typeof message !== 'string' || message.trim().length === 0) {
    res.status(400).json({ error: 'El parámetro "message" es obligatorio y debe ser texto.' });
    return;
  }
  if (!userId) {
    res.status(400).json({ error: 'El parámetro "userId" es obligatorio.' });
    return;
  }

  try {
    winstonLogger.info('Procesando mensaje de usuario en el controlador', { userId, chatId });
    
    // 2. Invocar la Capa de Servicio
    const responsePayload = await runAgentConversation(userId, message, chatId);
    
    // 3. Respuesta Exitosa Estructurada
    res.status(200).json({
      success: true,
      data: responsePayload
    });
  } catch (error) {
    winstonLogger.error('Error crítico en handleChatMessage', { error, userId, chatId });
    
    // 4. Delegar al Middleware Global de Manejo de Errores
    next(error);
  }
}
```

### B. Componente Frontend Premium (React + Vanilla CSS)
*Ubicación sugerida: `src/components/ChatBubble.tsx`*

```typescript
import React from 'react';
import './ChatBubble.css'; // Estilos específicos del componente

interface MessageProps {
  id: string;
  role: 'user' | 'model' | 'system';
  content: string;
  timestamp: Date;
}

/**
 * Componente funcional para renderizar los globos de texto del chat
 */
export const ChatBubble: React.FC<{ message: MessageProps }> = ({ message }) => {
  const isModel = message.role === 'model';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return <div className="chat-bubble-system">{message.content}</div>;
  }

  return (
    <div className={`chat-bubble-wrapper ${isModel ? 'bot' : 'user'}`}>
      <div className="chat-bubble-avatar">
        {isModel ? '🤖' : '👨‍💻'}
      </div>
      <div className="chat-bubble-content">
        <div className="chat-bubble-sender">
          {isModel ? 'Mentor Alura' : 'Tú'}
        </div>
        <div className="chat-bubble-text">
          {/* Aquí se puede integrar una librería como react-markdown */}
          <p>{message.content}</p>
        </div>
        <span className="chat-bubble-time">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
};
```

*Estilos CSS asociados del Componente ChatBubble (`src/components/ChatBubble.css`):*
```css
.chat-bubble-wrapper {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  max-width: 80%;
  animation: fadeIn 0.3s ease-in-out;
}

.chat-bubble-wrapper.user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.chat-bubble-content {
  background: var(--bg-glass);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-m);
  padding: 12px 16px;
  color: var(--text-main);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(8px);
}

.chat-bubble-wrapper.bot .chat-bubble-content {
  border-left: 3px solid var(--accent-color);
}

.chat-bubble-wrapper.user .chat-bubble-content {
  background: rgba(12, 76, 245, 0.15);
  border-color: rgba(12, 76, 245, 0.3);
}

.chat-bubble-sender {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.chat-bubble-time {
  font-size: 0.7rem;
  color: var(--text-muted);
  display: block;
  text-align: right;
  margin-top: 4px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
```

---

## 🌲 5. Convenciones de Git y Calidad del Código

- **Ramas de Desarrollo**: Queda prohibido hacer commits directos a `main`. Todo desarrollo debe provenir de una rama hija y pasar por revisión.
- **Flujo de Integración**:
  ```bash
  # 1. Crear rama de cambios
  git checkout -b feature/integracion-rag
  
  # 2. Confirmar los cambios con Conventional Commits
  git commit -m "feat: implementar busqueda semantica de embeddings en Postgres"
  
  # 3. Empujar la rama local
  git push origin feature/integracion-rag
  ```
- **Umbral de Calidad**:
  - Las pruebas unitarias deben tener un mínimo de **80% de cobertura** en la capa de Servicios y RAG.
  - El código de TypeScript no debe contener advertencias del compilador ni errores linter antes de abrir el PR.
