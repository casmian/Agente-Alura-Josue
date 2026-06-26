# Manual de Prácticas de Pruebas y Calidad de Software (QA) — Neouniverse 🧪📋

Este manual establece los estándares de calidad de software y las directrices para la escritura de pruebas automatizadas en **Neouniverse**. Su objetivo es garantizar la robustez, mantenibilidad y escalabilidad del código fuente de nuestras aplicaciones.

---

## 📐 1. Pirámide de Pruebas en Neouniverse

Nuestra estrategia de QA se basa en una distribución balanceada de pruebas:

* **Pruebas Unitarias (70%)**: Validación aislada de funciones, componentes y utilidades. Deben ser rápidas de ejecutar y no depender de servicios externos.
* **Pruebas de Integración (20%)**: Validación de la interacción de múltiples módulos o llamadas a bases de datos y APIs locales.
* **Pruebas de Extremo a Extremo / E2E (10%)**: Flujos de usuario completos ejecutados sobre el navegador web o la interfaz simulando las acciones de un usuario final.

---

## 🛠️ 2. Estándares Técnicos para Pruebas Unitarias

### A. Frontend (React + Vite)
Utilizamos **Vitest** y **React Testing Library** para las pruebas unitarias y de componentes frontend.

* **Regla de Cobertura**: Se exige un mínimo de **80% de cobertura de líneas** en todos los componentes interactivos del cliente.
* **Aislamiento**: Todo servicio de red o API de terceros debe simularse mediante mocks o MSW (Mock Service Worker).

Ejemplo de estructura recomendada para pruebas de componentes:
```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

describe('Componente Button', () => {
  it('debe renderizar el texto correctamente', () => {
    render(<Button label="Guardar" />);
    expect(screen.getByText('Guardar')).toBeInTheDocument();
  });
});
```

### B. Backend (Node.js & Python)
* **Frameworks**: Utilizamos **Jest** para Express/Node.js y **PyTest** para módulos y servicios en Python.
* **Bases de Datos**: Se prohíbe realizar pruebas unitarias contra bases de datos en producción o de staging. Se debe usar una base de datos local temporal o mocks dedicados de persistencia.

---

## 🚨 3. Políticas de Calidad y Criterios de Aceptación

Para que una nueva funcionalidad se considere terminada (*Definition of Done*), debe cumplir los siguientes criterios de calidad:

1. **Sin Errores en Pruebas**: Todas las pruebas locales y de integración deben pasar con éxito.
2. **Cobertura Mínima**: Se verifica en el pipeline de CI/CD que el nuevo código mantenga o supere los estándares de cobertura exigidos.
3. **Análisis de Vulnerabilidades**: El código debe estar libre de vulnerabilidades críticas o mayores detectadas por herramientas automatizadas.
4. **Revisión por Pares (Peer Review)**: Código limpio que cumpla con los estándares de estilo de TypeScript/Python y sea legible para otros desarrolladores.
