# Guía de Configuración y Despliegue Continuo (CI/CD) — Neouniverse 🚀🔄

Este documento establece el estándar oficial para la integración y despliegue continuo en **Neouniverse**. Define las reglas para el ciclo de vida del código, desde que un desarrollador crea una rama local hasta que el software se ejecuta en producción.

---

## 💻 1. Flujo de Git y Ciclo de Ramas

En Neouniverse utilizamos **GitFlow simplificado** para gestionar el ciclo de vida de nuestras aplicaciones.

### A. Ramas Principales
* **`main`**: Representa el código estable en producción. Solo se despliega mediante pipelines aprobados tras la validación en staging. No se permiten commits directos.
* **`develop`**: Rama de integración donde se consolidan las nuevas características. De aquí parten las ramas de características.

### B. Ramas de Soporte
* **`feature/[ID-Ticket]-[descripcion]`**: Para el desarrollo de nuevas tareas. Parten de `develop` y se reintegran mediante Pull Requests.
* **`hotfix/[descripcion]`**: Ramas urgentes para resolver incidentes SEV 1 en producción. Parten de `main` y se integran tanto en `main` como en `develop`.

---

## 🛠️ 2. Flujo de Integración Continua (CI)

Cada Pull Request (PR) hacia la rama `develop` o `main` activa de forma automática nuestro pipeline de GitHub Actions. Las siguientes comprobaciones son obligatorias:

1. **Linter y Formateo**: Ejecución de `npm run lint` para garantizar que el código se alinee con las guías de estilo oficiales.
2. **Pruebas Unitarias**: Todo el conjunto de pruebas unitarias debe ejecutarse sin errores (`npm run test`).
3. **Análisis Estático (Sonarqube)**: Se evalúa que no se introduzcan vulnerabilidades de seguridad y que el código duplicado se mantenga por debajo del 5%.

> [!IMPORTANT]
> Ningún Pull Request podrá mezclarse (merge) si alguna de estas comprobaciones falla o si no cuenta con la aprobación de al menos un **Tech Lead**.

---

## ☁️ 3. Pipeline de Despliegue Continuo (CD) en OCI

El despliegue en la nube de **Oracle Cloud Infrastructure (OCI)** está completamente automatizado y configurado según los entornos:

### A. Entorno de Staging (Pruebas)
* **Desencadenador**: Todo merge exitoso en la rama `develop`.
* **Proceso**: El pipeline de CI/CD empaqueta la aplicación en una imagen Docker, la sube a OCI Container Registry y reinicia la instancia de cómputo en el entorno de pruebas para validar los cambios.

### B. Entorno de Producción
* **Desencadenador**: Creación de una etiqueta de versión (release tag, ej: `v1.2.0`) en la rama `main`.
* **Proceso**:
  1. Compilación y optimización de assets.
  2. Subida de la nueva versión de la imagen Docker al Registro de OCI.
  3. Despliegue progresivo (*rolling updates*) en las instancias de OCI Compute detrás del balanceador de carga.
  4. Ejecución automática de las migraciones de base de datos PostgreSQL utilizando comandos seguros.
