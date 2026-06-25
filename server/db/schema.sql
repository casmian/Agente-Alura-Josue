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

-- 4. Tabla de Embeddings de Conocimiento (RAG)
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_nombre VARCHAR(150) NOT NULL, -- Nombre del archivo de origen (ej. guia_estilo.md)
    categoria VARCHAR(50) NOT NULL,        -- Categoría (Entorno, Estilo, Arquitectura)
    contenido TEXT NOT NULL,                -- Fragmento de texto extraído
    embedding VECTOR(1536),                 -- Vector de 1536 dimensiones (Gemini/OpenAI compatible)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear un índice IVFFlat para acelerar búsquedas vectoriales por similitud de coseno
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
