# Manual de Onboarding para Nuevos Desarrolladores — Santos Pegasus Soluciones 🛠️🚀

Este manual contiene las instrucciones detalladas para desplegar de forma local y en la nube de **Oracle Cloud Infrastructure (OCI)** el ecosistema del **Agente Alura** en **Santos Pegasus Soluciones**.

---

## 📋 1. Requisitos Previos Generales

Antes de iniciar la instalación en Santos Pegasus Soluciones, asegúrate de tener configurados los siguientes componentes:

### A. Entorno de Ejecución (Node.js)
- **Versión requerida**: Node.js v20.x LTS o superior.
- **Gestor de versiones recomendado**: `nvm` (Node Version Manager).

### B. Sistema Gestor de Base de Datos
- **Opción Local**: Docker con PostgreSQL y la extensión `pgvector` habilitada:
  ```bash
  docker run --name pg-pegasus-agent -e POSTGRES_PASSWORD=pegasus_secure_pass -e POSTGRES_DB=pegasus_db -p 5432:5432 -d ankane/pgvector:v0.5.1
  ```
- **Opción Nube (OCI)**: Base de datos **OCI PostgreSQL** administrada o ejecutada dentro de un contenedor en OCI Compute.

---

## ☁️ 2. Guía de Despliegue en Oracle Cloud Infrastructure (OCI)

Para cumplir con las directrices operativas de Santos Pegasus Soluciones, utilizaremos al menos un servicio en la nube de OCI. A continuación se detalla la configuración recomendada:

### Opción A: Despliegue en una Instancia de Cómputo (OCI Compute VM) - *Nivel Gratuito de OCI (Always Free)*
1. **Crear Instancia**:
   - Ve a la consola de OCI y crea una instancia de cómputo VM (recomendado: Ubuntu Server o Oracle Linux).
   - Descarga la clave SSH de acceso.
2. **Configurar Red Virtual (VCN)**:
   - En las Listas de Seguridad de tu VCN, añade una **regla de ingreso** para habilitar el puerto de la aplicación (ejemplo: puerto `80` o `3000` para Express/Vite) permitiendo tráfico desde `0.0.0.0/0`.
3. **Conexión e Instalación**:
   - Conéctate por SSH a la máquina:
     ```bash
     ssh -i <clave_privada> ubuntu@<IP_PÚBLICA_OCI>
     ```
   - Instala Node.js, Git y Docker en la máquina de OCI.
4. **Despliegue del Proyecto**:
   - Clona el repositorio público de GitHub en la VM.
   - Crea el archivo `.env` en la máquina con tus credenciales de base de datos y la clave `GEMINI_API_KEY`.
   - Inicia los servicios con un manejador de procesos como `pm2` para mantener la ejecución en segundo plano:
     ```bash
     sudo npm install pm2 -g
     pm2 start dist/server/index.js --name "agente-alura"
     ```

### Opción B: Integración de Almacenamiento (OCI Object Storage)
Para el soporte de archivos de la empresa:
1. Crea un **Bucket** en OCI Object Storage llamado `pegasus-agent-knowledge`.
2. Genera credenciales de acceso de API de OCI (Customer Secret Key) para interactuar mediante el SDK de OCI (`@oracle/oci-sdk`) en el backend.
3. El backend descargará y leerá dinámicamente los archivos de este Bucket para procesar sus contenidos y extraer los embeddings.

---

## 🗄️ 3. Estructura del Esquema de Base de Datos (SQL)

Ejecuta el script de migración (`npm run db:migrate`) para crear la base de datos relacional y vectorial en PostgreSQL:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla de Usuarios (Colaboradores)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Sesiones de Chat
CREATE TABLE IF NOT EXISTS chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    titulo VARCHAR(200) DEFAULT 'Nueva Conversación',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Mensajes
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user', 'model'
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Conocimientos Extraídos y Embeddings (RAG)
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_nombre VARCHAR(150) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    contenido TEXT NOT NULL,
    ubicacion_exacta VARCHAR(200) NOT NULL,
    autor_responsable VARCHAR(100) NOT NULL,
    ultima_actualizacion TIMESTAMP WITH TIME ZONE NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índice optimizado HNSW para consultas de similitud de coseno vectoriales
CREATE INDEX IF NOT EXISTS document_chunks_hnsw_idx 
ON document_chunks USING hnsw (embedding vector_cosine_ops);
```

---

## 📁 4. Tubería de Procesamiento de Documentos Multiformato

El servidor backend integra las siguientes librerías de Node.js para analizar dinámicamente los archivos en memoria o descargados de OCI Object Storage:

| Formato | Extensión | Librería de Ingesta y Extracción de Texto |
| :--- | :--- | :--- |
| **PDF** | `.pdf` | `pdf-parse` (extrae texto y número de página) |
| **Word** | `.docx` | `mammoth` (convierte DOCX a texto limpio o HTML) |
| **Excel** | `.xlsx`, `.xls` | `xlsx` / SheetJS (lee celdas, filas y las convierte a JSON/CSV) |
| **PowerPoint** | `.pptx` | `officeparser` (analiza las diapositivas de texto) |
| **Markdown** | `.md` | Lectura directa de texto UTF-8 |
| **CSV** | `.csv` | `csv-parser` o parseador de cadenas nativo |
| **JSON** | `.json` | `JSON.parse` estructurado |
| **HTML** | `.html` | `cheerio` (para limpiar etiquetas y extraer contenido de texto) |

---

## 🔑 5. Configuración del Archivo .env

Crea el archivo `.env` en la raíz del proyecto. Asegúrate de configurar los valores correspondientes para Santos Pegasus Soluciones:

```env
PORT=3000
NODE_ENV=development

# Base de datos PostgreSQL (local o instancia de OCI)
DATABASE_URL="postgresql://postgres:pegasus_secure_pass@localhost:5432/pegasus_db?schema=public&sslmode=disable"

# Clave de API de Gemini
GEMINI_API_KEY="AIzaSyYourSecretAPIKeyGoesHere"

# OCI Object Storage (Opcional - para integración remota de archivos)
OCI_NAMESPACE="your-oci-namespace"
OCI_BUCKET_NAME="pegasus-agent-knowledge"
OCI_REGION="us-ashburn-1"
```

---

## 🏃 6. Comandos de Ejecución y Despliegue

```bash
# 1. Instalar dependencias
npm install

# 2. Correr migraciones de base de datos
npm run db:migrate

# 3. Poblar RAG con archivos de prueba locales
npm run db:seed

# 4. Iniciar en modo desarrollo
npm run dev
```

---

## 🔍 7. Diagnóstico de Despliegue en OCI
* **Fallo**: No puedo acceder al chat desde internet usando la IP pública de OCI.
* **Solución**:
  1. Revisa que el puerto esté abierto en el Firewall interno de Linux de tu VM:
     ```bash
     sudo ufw allow 3000/tcp
     sudo ufw reload
     ```
  2. Confirma en la consola web de OCI que la **Lista de Seguridad** de la subred tenga una regla de entrada (Ingress Rule) activa para el puerto `3000` desde la dirección fuente `0.0.0.0/0`.
