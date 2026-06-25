# Manual de Configuración del Entorno de Desarrollo 🛠️🚀

Este documento detalla el procedimiento completo paso a paso para configurar tu entorno local y poner en marcha el proyecto del **Agente Alura**. Sigue estas instrucciones cuidadosamente para evitar problemas de compatibilidad o variables de entorno vacías.

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instaladas las siguientes herramientas en tu sistema operativo:

1. **Node.js** (Versión 20.x LTS o superior recomendado)
   - [Descargar Node.js](https://nodejs.org/)
   - Verifica la versión ejecutando: `node -v`
2. **PostgreSQL** (Versión 15.x o superior con extensión `pgvector` instalada)
   - [Descargar PostgreSQL](https://www.postgresql.org/)
   - Para instalar `pgvector` en sistemas locales, consulta la guía oficial de la extensión o usa un contenedor Docker:
     ```bash
     docker run --name postgres-vector -e POSTGRES_PASSWORD=mysecretpassword -p 5432:5432 -d ankane/pgvector
     ```
3. **Git** (Para control de versiones)
   - [Descargar Git](https://git-scm.com/)

---

## ⚡ Paso 1: Clonar e Instalar Dependencias

Abre la terminal en la carpeta raíz del proyecto y ejecuta:

```bash
# Instalar las dependencias de Node.js
npm install
```

---

## 🔑 Paso 2: Configuración de Variables de Entorno

El backend requiere claves de API y accesos a la base de datos para funcionar. 

1. Copia el archivo de plantilla `.env.example` y crea un nuevo archivo llamado `.env` en la raíz del proyecto:
   ```bash
   cp .env.example .env
   ```
2. Abre el archivo `.env` y rellena las siguientes variables con tus valores:
   ```env
   # Puerto en el que correrá el servidor express backend
   PORT=3000
   
   # Conexión local a PostgreSQL (con la extensión pgvector activa)
   DATABASE_URL="postgresql://postgres:mysecretpassword@localhost:5432/agente_alura?schema=public"
   
   # Clave de API de Google Gemini (Vertex AI / Google AI Studio)
   GEMINI_API_KEY="AIzaSyYourActualKeyHere..."
   
   # Nivel de registro de consola (debug, info, warn, error)
   LOG_LEVEL="info"
   ```

---

## 🗄️ Paso 3: Inicializar la Base de Datos

Para crear las tablas de usuarios, chats, logs y activar la extensión vectorial de PostgreSQL, ejecuta el script de migración:

```bash
# Ejecutar las migraciones de base de datos
npm run db:migrate
```

Para poblar la base de datos con los contenidos por defecto de los cursos de Alura (embeddings para RAG), ejecuta el seeder:

```bash
# Rellenar embeddings de cursos e información base
npm run db:seed
```

---

## 🏃 Paso 4: Ejecutar el Proyecto en Modo Desarrollo

Una vez completada la configuración de la base de datos y variables de entorno, puedes iniciar la aplicación:

```bash
# Iniciar frontend y backend simultáneamente en modo desarrollo
npm run dev
```

El servidor web estará disponible en:
- **Frontend App**: `http://localhost:5173` (Vite)
- **Backend API**: `http://localhost:3000` (Express)

---

## 🧪 Paso 5: Ejecutar Pruebas y Validación

Antes de enviar un Pull Request, ejecuta los tests locales para validar la lógica del agente:

```bash
# Ejecutar suite de pruebas unitarias y de integración
npm run test
```
