# Guía de Estilo de Código y Buenas Prácticas 📖✨

Para mantener el código del **Agente Alura** limpio, legible y escalable, todos los desarrolladores (humanos e inteligencias artificiales) deben seguir estrictamente estas reglas de estilo y flujos de trabajo.

---

## 💻 1. Convenciones de Nomenclatura (Naming Conventions)

* **Variables y Funciones**: Usa `camelCase`.
  ```typescript
  const studentProfile = fetchStudentProfile(studentId);
  ```
* **Clases, Interfaces y Tipos (Types)**: Usa `PascalCase`.
  ```typescript
  interface AgentConfig {
    temperature: number;
    modelName: string;
  }
  ```
* **Constantes y Variables de Entorno**: Usa `UPPER_CASE` con guiones bajos.
  ```typescript
  const DEFAULT_MAX_TOKENS = 2048;
  ```
* **Componentes de React**: Usa `PascalCase` para el archivo y la función del componente.
  ```typescript
  // ChatBubble.tsx
  export function ChatBubble() { ... }
  ```

---

## 🛡️ 2. Reglas de TypeScript

* **Evita el tipo `any`**: Todos los tipos deben estar declarados de forma explícita. Si el tipo es verdaderamente dinámico, usa `unknown` y realiza una comprobación de tipo.
* **Tipado de Retorno**: Define siempre el tipo de retorno en las funciones públicas del sistema o endpoints de la API.
  ```typescript
  async function generateFeedback(code: string): Promise<string> { ... }
  ```
* **Interfaces sobre Tipos**: Prefiere usar `interface` para definir estructuras de objetos que pueden ser extendidas, y `type` para uniones o tipos primitivos.

---

## 🎨 3. Reglas de Estilo UI/UX (Frontend CSS)

* **Vanilla CSS**: Prohibido usar TailwindCSS u otros frameworks de utilidades a menos que se indique lo contrario. Usa CSS puro.
* **Diseño Responsivo**: Emplea Flexbox y CSS Grid para layouts fluidos. Usa consultas de medios (`@media`) para adaptar la pantalla a dispositivos móviles.
* **Variables CSS**: Centraliza colores, espaciados y fuentes en `:root` dentro de `index.css`.
  ```css
  :root {
    --primary-color: #0d4bf2;
    --background-dark: #090b11;
    --font-main: 'Outfit', sans-serif;
  }
  ```
* **Micro-animaciones**: Utiliza `transition` suave (`ease-in-out` de 0.2s o 0.3s) para efectos de cursor flotante (*hover*) en botones, clicks y transiciones de estados del chat.

---

## 🌲 4. Flujo de Git y Convenciones de Commit

### Nombres de Ramas (Branches)
Usa los siguientes prefijos para las ramas según el tipo de cambio:
- `feature/`: Nuevas funcionalidades (ej. `feature/integracion-rag`).
- `bugfix/`: Corrección de errores (ej. `bugfix/chat-scroll-error`).
- `docs/`: Actualizaciones de documentación (ej. `docs/guia-estilo`).
- `refactor/`: Cambios en el código que no añaden funciones ni corrigen bugs.

### Convención de Commits (Conventional Commits)
Los mensajes de commit deben seguir este formato de prefijos en minúscula:
* `feat: ...` -> Nueva funcionalidad.
* `fix: ...` -> Corrección de un error.
* `docs: ...` -> Cambios en la documentación.
* `style: ...` -> Formateo o cambios visuales (CSS) sin alterar el comportamiento.
* `refactor: ...` -> Refactorización de código.

*Ejemplo*: `feat: implementar function calling para busqueda web en el agente`

---

## 📥 5. Requisitos para Pull Requests (PR)

Antes de enviar un Pull Request a la rama `main`:
1. El código no debe tener errores de compilación (`npm run build` debe pasar con éxito).
2. No debe haber errores de análisis estático (ejecutar `npm run lint`).
3. Todas las pruebas automatizadas deben pasar sin fallos (`npm run test`).
4. Cada Pull Request debe ir acompañado de una breve descripción que resuma qué cambia y cómo probarlo.
