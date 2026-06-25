# Guía Oficial de Ingeniería Front-end — Santos Pegasus Soluciones 📖✨

Este documento establece las directrices oficiales de codificación, las arquitecturas recomendadas y los estándares de diseño para el desarrollo frontend en **Santos Pegasus Soluciones**.

---

## 🏗️ 1. Estándar de Estilos CSS (Vanilla CSS Token System)

Para mantener la excelencia visual e interactiva en las aplicaciones de Santos Pegasus Soluciones sin frameworks externos, se utiliza un sistema de diseño basado en variables de CSS (`CSS Custom Properties`) definidas globalmente:

```css
:root {
  /* Paleta de Colores (Diseño Modo Oscuro Premium) */
  --bg-primary: #07090e;
  --bg-secondary: #101423;
  --bg-glass: rgba(16, 20, 35, 0.65);
  --accent-color: #0c4cf5;
  --accent-glow: rgba(12, 76, 245, 0.35);
  --text-main: #f0f3f8;
  --text-muted: #8c9bb4;
  --border-color: rgba(140, 155, 180, 0.12);
  
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

## 💻 2. Estructura y Plantilla de Componente React (TypeScript)

Los componentes deben ser modulares, tipados de forma estricta y libres de dependencias de estilos ad-hoc. A continuación se expone la estructura recomendada para un componente de mensajería:

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
          {isModel ? 'Mentor Cognitivo' : 'Tú'}
        </div>
        <div className="chat-bubble-text">
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

---

## 🎨 3. Estilos CSS del Componente ChatBubble (`ChatBubble.css`)

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

## 📋 4. Convenciones de Calidad Frontend
- **No TailwindCSS**: Se debe utilizar Vanilla CSS nativo organizado por variables.
- **Tipos de Datos**: Prohibido usar `any`. Todos los componentes y hooks deben declarar interfaces TypeScript claras.
- **Persistencia**: El estado de sesión debe guardarse localmente utilizando `LocalStorage` para evitar la pérdida de chats durante recargas de navegador.
