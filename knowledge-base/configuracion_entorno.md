# Manual de Configuración del Entorno de Desarrollo (Nivel Empresarial) 🛠️🚀

Este manual contiene las instrucciones detalladas para desplegar de forma local y segura el proyecto del **Agente Alura**. Está diseñado para cubrir múltiples sistemas operativos y entornos virtuales, garantizando una configuración homogénea para todo el equipo.

---

## 📋 1. Requisitos Previos Generales

Antes de iniciar la instalación de dependencias, asegúrate de tener configurados los siguientes componentes:

### A. Entorno de Ejecución (Node.js)
- **Versión requerida**: Node.js v20.x LTS o superior.
- **Gestor de paquetes**: npm v10.x o superior (incluido con Node.js).
- *Recomendación*: Utilizar un gestor de versiones como `nvm` (Node Version Manager) para evitar conflictos:
  ```bash
  # Instalar Node.js v20 LTS usando nvm
  nvm install 20
  nvm use 20
  ```

### B. Sistema Gestor de Base de Datos (PostgreSQL)
- **Versión requerida**: PostgreSQL v15 o v16.
- **Extensión obligatoria**: `pgvector` (para almacenamiento y búsqueda de embeddings de vectores).
- **Opción Recomendada (Docker)**: La forma más rápida de ejecutar PostgreSQL con la extensión vector preconfigurada es mediante Docker:
  ```bash
  # Descargar e iniciar la imagen oficial de pgvector
  docker run --name pg-agente-alura -e POSTGRES_PASSWORD=alura_secure_pass -e POSTGRES_DB=agente_alura -p 5432:5432 -d ankane/pgvector:v0.5.1
  ```

---

## 💻 2. Guía de Configuración por Sistema Operativo

### Windows (Instalación Nativa)
1. Instala Node.js desde el instalador oficial `.msi`.
2. Si prefieres PostgreSQL nativo en lugar de Docker:
   - Descarga PostgreSQL de [EnterpriseDB](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads).
   - Descarga los binarios de `pgvector` desde su repositorio de GitHub y copia el archivo `vector.dll` en la carpeta `lib/` de PostgreSQL y los scripts `.sql` asociados en `share/extension/`.
3. Asegúrate de configurar las variables de entorno de Windows agregando la ruta de instalación de PostgreSQL al `PATH` del sistema (ej. `C:\Program Files\PostgreSQL\16\bin`).

### macOS (Homebrew)
1. Instala Node.js y PostgreSQL mediante Homebrew:
   ```bash
   brew install node@20 postgresql@15
   ```
2. Instala la extensión `pgvector`:
   ```bash
   brew install pgvector
   ```
3. Inicia el servicio de base de datos local:
   ```bash
   brew services start postgresql@15
   ```

### Linux (Ubuntu/Debian)
1. Instala Node.js:
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```
2. Instala PostgreSQL y sus herramientas de desarrollo:
   ```bash
   sudo apt-get install -y postgresql postgresql-server-dev-all
   ```
3. Compila e instala `pgvector`:
   ```bash
   git clone https://github.com/pgvector/pgvector.git
   cd pgvector
   make
   sudo make install
   ```

---

## 🗄️ 3. Estructura del Esquema de Base de Datos (SQL)

La base de datos del Agente Alura se compone de cuatro tablas principales. El script de inicialización (`npm run db:migrate`) ejecutará el siguiente modelo relacional en PostgreSQL:

```sql
-- Habilitar la extensión para manejo de vectores
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Tabla de Usuarios (Estudiantes de Alura)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    rol VARCHAR(30) DEFAULT 'student', -- 'student', 'admin', 'moderator'
    progreso_tecnologico JSONB, -- Historial de cursos y tecnologías finalizados
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de Sesiones de Conversación
CREATE TABLE IF NOT EXISTS chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    titulo VARCHAR(200) DEFAULT 'Nueva Conversación',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabla de Mensajes del Historial de Chat
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user', 'model', 'system'
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tabla de Conocimientos y Embeddings (RAG)
CREATE TABLE IF NOT EXISTS course_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    curso_nombre VARCHAR(150) NOT NULL,
    clase_titulo VARCHAR(200) NOT NULL,
    url_fuente VARCHAR(255),
    contenido TEXT NOT NULL,
    embedding VECTOR(1536), -- Vector de 1536 dimensiones para embeddings de Gemini/OpenAI
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear un índice IVFFlat para acelerar búsquedas vectoriales por similitud de coseno
CREATE INDEX IF NOT EXISTS course_embeddings_idx 
ON course_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## 🔑 4. Configuración de Variables de Entorno (.env)

Crea el archivo `.env` en la raíz del proyecto. Asegúrate de configurar los valores de producción y desarrollo según corresponda:

```env
# ==========================================
# CONFIGURACIÓN DEL SERVIDOR BACKEND
# ==========================================
PORT=3000
NODE_ENV=development # 'development', 'production', 'test'
LOG_LEVEL=debug # 'debug', 'info', 'warn', 'error'

# ==========================================
# CONEXIÓN DE BASE DE DATOS (POSTGRESQL)
# ==========================================
# Ajusta el usuario, contraseña, host y base de datos según tu instalación local
DATABASE_URL="postgresql://postgres:alura_secure_pass@localhost:5432/agente_alura?schema=public&sslmode=disable"
DB_POOL_MIN=2
DB_POOL_MAX=10

# ==========================================
# INTEGRACIÓN CON INTELIGENCIA ARTIFICIAL (GEMINI)
# ==========================================
# Obtén tu clave en Google AI Studio o Vertex AI Console
GEMINI_API_KEY="AIzaSyYourSecretAPIKeyGoesHere"
GEMINI_MODEL_NAME="gemini-2.0-flash" # Modelo recomendado para chat rápido y herramientas
GEMINI_TEMPERATURE=0.2 # Valor bajo para respuestas precisas y socráticas
```

---

## 🚀 5. Comandos de Ejecución y Despliegue

Instala las dependencias y prepara el entorno con los siguientes comandos:

```bash
# 1. Instalar paquetes de producción y desarrollo
npm install

# 2. Correr migraciones de base de datos (creación de tablas e índices)
npm run db:migrate

# 3. Poblar la base de datos con los datos de conocimiento RAG (CSV Seeds)
npm run db:seed

# 4. Iniciar la aplicación en modo desarrollo (Hot-Reload activo)
npm run dev

# 5. Compilar la aplicación para producción (TypeScript a JavaScript puro y empaquetado Vite)
npm run build

# 6. Iniciar el servidor compilado en producción
npm run start
```

---

## 🔍 6. Sección de Diagnóstico y Resolución de Problemas (Troubleshooting)

### Error A: `Database connection timed out` o `ECONNREFUSED`
* **Causa**: El servidor PostgreSQL no se está ejecutando o el host/puerto en `DATABASE_URL` es incorrecto.
* **Solución**:
  1. Verifica que el contenedor de Docker esté activo con `docker ps`. Si no está activo, inícialo con `docker start pg-agente-alura`.
  2. Si PostgreSQL es nativo, confirma que el servicio esté corriendo en el puerto `5432` con `pg_isready` (en macOS/Linux) o abriendo el Administrador de Servicios (en Windows).

### Error B: `extension "vector" is not available` o `could not open extension control file`
* **Causa**: PostgreSQL se está ejecutando, pero la extensión `pgvector` no se instaló correctamente en el sistema.
* **Solución**:
  1. Si usas Docker, asegúrate de estar utilizando la imagen `ankane/pgvector` en lugar de la imagen oficial básica de Postgres.
  2. Si es una instalación nativa, repite el proceso de compilación y copia del archivo `.dll` o `.so` en las carpetas correspondientes de PostgreSQL.

### Error C: `API key not found` o `403 Forbidden` al invocar a Gemini
* **Causa**: La variable `GEMINI_API_KEY` en el archivo `.env` está vacía, contiene espacios o la clave de API ha expirado.
* **Solución**:
  1. Verifica que no haya comillas o espacios extras alrededor de la API key en tu archivo `.env`.
  2. Haz una prueba curl directa para descartar bloqueos de red corporativos:
     ```bash
     curl -H "Content-Type: application/json" -d "{'contents':[{'parts':[{'text':'Hola'}]}]}" "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=TU_API_KEY"
     ```

### Error D: `Port 3000 is already in use`
* **Causa**: Otro proceso del sistema está utilizando el puerto del backend.
* **Solución**:
  - Cambia el puerto en tu archivo `.env` (ej. `PORT=3001`).
  - O busca y finaliza el proceso que bloquea el puerto:
    - *Windows*: `netstat -ano | findstr :3000` y luego `taskkill /PID <PID_PROCESO> /F`.
    - *macOS/Linux*: `lsof -i :3000` y luego `kill -9 <PID>`.
