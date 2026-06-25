-- Habilitar la extensión vectorial en PostgreSQL
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Tabla de Usuarios (Colaboradores y Estudiantes)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de Sesiones de Chat
CREATE TABLE IF NOT EXISTS chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    titulo VARCHAR(200) DEFAULT 'Nueva Conversación',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabla de Mensajes de Conversaciones
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user', 'model'
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tabla de Embeddings de Conocimiento (RAG con Metadatos Detallados)
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_nombre VARCHAR(150) NOT NULL,    -- Nombre del archivo (ej. guia_estilo.md)
    categoria VARCHAR(50) NOT NULL,            -- Categoría (Entorno, Estilo, Arquitectura)
    contenido TEXT NOT NULL,                    -- Fragmento de texto extraído
    ubicacion_exacta VARCHAR(150),              -- Ubicación (Página X, Diapositiva Y, Filas A-B, Sección Z)
    autor_responsable VARCHAR(150),             -- Responsable del documento
    ultima_actualizacion TIMESTAMP WITH TIME ZONE, -- Fecha de modificación del archivo
    embedding VECTOR(1536),                     -- Vector de embeddings de 1536 dimensiones
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================================
-- OPTIMIZACIONES DE INDEXACIÓN (ETAPA 3)
-- =========================================================================

-- A. Crear un índice HNSW (Hierarchical Navigable Small World) para búsquedas vectoriales veloces y precisas
CREATE INDEX IF NOT EXISTS document_chunks_hnsw_idx 
ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- B. Crear índices tradicionales B-Tree en metadatos para permitir filtrado estructurado veloz
CREATE INDEX IF NOT EXISTS document_chunks_categoria_idx ON document_chunks (categoria);
CREATE INDEX IF NOT EXISTS document_chunks_documento_nombre_idx ON document_chunks (documento_nombre);
CREATE INDEX IF NOT EXISTS document_chunks_autor_responsable_idx ON document_chunks (autor_responsable);
