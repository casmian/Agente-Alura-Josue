# Protocolo de Respuesta a Incidentes y Post-Mortems — Santos Pegasus Soluciones 🚨⚡

Este protocolo establece los procedimientos oficiales para la identificación, contención, resolución y análisis post-mortem de incidentes de seguridad y disponibilidad tecnológica en **Santos Pegasus Soluciones**.

---

## 🛑 1. Niveles de Severidad de Incidentes

Clasificamos los incidentes en tres niveles según el impacto en la operación de nuestros clientes y la infraestructura en la nube (OCI):

### 🔴 SEV 1 — Crítico (Impacto Alto)
* **Definición**: Interrupción total del servicio principal, violación de seguridad de datos de clientes, o caída de la infraestructura productiva sin redundancia activa.
* **Tiempo de Respuesta Objetivo**: < 15 minutos.
* **Canal de Comunicación**: Canal Slack `#incidentes-sev1` y llamada telefónica automatizada a ingenieros de guardia.

### 🟡 SEV 2 — Mayor (Impacto Medio)
* **Definición**: Degradación significativa de rendimiento en producción (latencia > 2000ms), fallos recurrentes en APIs secundarias, o inoperabilidad parcial de paneles de administración.
* **Tiempo de Respuesta Objetivo**: < 1 hora.
* **Canal de Comunicación**: Canal Slack `#incidentes-sev2`.

### 🔵 SEV 3 — Menor (Impacto Bajo)
* **Definición**: Bugs cosméticos en el frontend, fallos intermitentes no bloqueantes en desarrollo/staging, o retrasos menores en pipelines de CI/CD.
* **Tiempo de Respuesta Objetivo**: < 24 horas.

---

## 🏃 2. Flujo Operativo de Respuesta

Cuando se detecta una alerta de monitoreo en OCI:

1. **Declaración del Incidente**: El primer ingeniero en responder asume el rol de **Comandante del Incidente (IC)**.
2. **Contención**: Priorizar mitigar el impacto para los usuarios (ej. desviar tráfico a zona de respaldo, revertir el último despliegue o reiniciar contenedores).
3. **Resolución**: Implementar una solución permanente o parche caliente (hotfix).
4. **Cierre**: Validar con telemetría que el servicio opera bajo los umbrales normales de disponibilidad (SLA).

---

## ✍️ 3. Plantilla Oficial de Post-Mortem

Todo incidente de nivel SEV 1 y SEV 2 requiere la redacción de un documento Post-Mortem en un plazo máximo de 48 horas laborables.

### Estructura Requerida:

```markdown
# Post-Mortem: [Título Descriptivo del Incidente] (Fecha: AAAA-MM-DD)

## 📋 Resumen Ejecutivo
Breve explicación del fallo en términos de negocio (qué falló, a quiénes afectó y por cuánto tiempo).

## ⏱️ Cronología de Eventos
- **12:00 UTC**: Detección de la anomalía en telemetría de OCI.
- **12:05 UTC**: Declaración del incidente e inicio de contención.
- **12:20 UTC**: Aplicación del parche de mitigación.
- **12:30 UTC**: Confirmación de normalidad.

## 🔍 Análisis de Causa Raíz (Root Cause Analysis - RCA)
Explicación técnica detallada del factor desencadenante (los "5 Porqués").

## 🛠️ Acciones Correctivas (Action Items)
- [ ] Implementar reintentos con backoff exponencial. (Responsable: Backend Team)
- [ ] Ampliar reglas de alerta de memoria en OCI Compute. (Responsable: DevOps)
```
