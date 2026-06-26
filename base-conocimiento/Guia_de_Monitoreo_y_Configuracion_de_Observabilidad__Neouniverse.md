# Guía de Monitoreo y Configuración de Observabilidad — Neouniverse 📈🔍

Esta guía documenta los sistemas, herramientas y prácticas de observabilidad en **Neouniverse**. Define las reglas para la recolección de logs, métricas y trazas necesarias para diagnosticar la salud de la infraestructura y resolver incidentes con rapidez.

---

## 🛠️ 1. Las Tres Columnas de la Observabilidad

Para mantener la disponibilidad y el rendimiento de nuestros productos, estructuramos la observabilidad en tres áreas críticas:

### A. Registro de Eventos (Logs)
* **Logs de Aplicación**: Escritos en formato estructurado (JSON) a través de la salida estándar (`stdout`), lo que facilita su indexación automática en la nube.
* **Plataforma de Consulta**: Centralizados a través del servicio **OCI Logging**. Todo desarrollador con accesos de lectura puede auditar y buscar logs utilizando identificadores de traza (*Correlation IDs*).

### B. Métricas del Sistema
* Monitoreamos métricas clave de hardware y sistema operativo:
  * **Uso de CPU y Memoria**: Alertas automáticas si el uso excede el 85% durante más de 5 minutos consecutivos.
  * **Latencia de Red**: Monitoreo de latencia en peticiones a la API del Agente Alura (objetivo: < 500ms).
  * **Consumo de Almacenamiento**: Alertas preventivas para OCI Database y Object Storage.

### C. Rastreo de Peticiones (Tracing)
* Cada petición HTTP entrante cuenta con un ID único que se propaga por todos los microservicios. Esto permite identificar cuellos de botella en la comunicación interna.

---

## 🚨 2. Canales y Políticas de Alertas

Nuestras alertas se configuran para evitar la fatiga y priorizar los problemas de forma ordenada:

* **Alertas Críticas (SEV 1)**:
  * **Definición**: Pérdida de conectividad de base de datos, caídas completas de la API, o tasas de error HTTP 5xx superiores al 10% en un minuto.
  * **Canal**: Envío inmediato al canal Slack `#incidentes-sev1` y llamadas automáticas mediante servicios de notificación al desarrollador de guardia (*On-Call engineer*).
* **Alertas Modificadas (SEV 2)**:
  * **Definición**: Latencia superior a 2500ms en el RAG, fallos aislados en servicios complementarios.
  * **Canal**: Canal Slack `#soporte-ti` y notificaciones internas por correo electrónico.

---

## 🔍 3. Diagnóstico Técnico y Solución de Problemas

Cuando se detecte una degradación en el rendimiento del RAG:
1. **Comprobar Conectividad de DB**: Verificar si OCI PostgreSQL está respondiendo consultas básicas.
2. **Revisar Cuota de API de Gemini**: Auditar si el error reporta `429 Resource Exhausted` (Límites de cuota excedidos en el SDK).
3. **Analizar Logs Recientes**: Filtrar por el identificador de la sesión afectada en el visor de OCI Logging para encontrar trazas específicas.
