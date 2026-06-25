import * as fs from 'fs';
import * as path from 'path';
import * as dotenv from 'dotenv';
import { GoogleGenAI } from '@google/genai';
import { dbQuery, dbPool } from '../db/client';
import { extractTextFromFile } from './documentParser';

dotenv.config();

const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
if (!GEMINI_API_KEY) {
  console.error('Error: La variable de entorno GEMINI_API_KEY no está configurada.');
  process.exit(1);
}

// Inicializar el SDK de Google Gen AI
const ai = new GoogleGenAI({ apiKey: GEMINI_API_KEY });

/**
 * Divide un texto plano en fragmentos (chunks) más pequeños con solapamiento (overlap)
 */
function chunkText(text: string, chunkSize: number = 1000, overlap: number = 150): string[] {
  const chunks: string[] = [];
  let currentIndex = 0;
  
  while (currentIndex < text.length) {
    let endIndex = currentIndex + chunkSize;
    
    // Si no estamos al final del texto, intentar cortar en un espacio en blanco o salto de línea
    if (endIndex < text.length) {
      const lastSpace = text.lastIndexOf(' ', endIndex);
      if (lastSpace > currentIndex) {
        endIndex = lastSpace;
      }
    }
    
    const chunk = text.substring(currentIndex, endIndex).trim();
    if (chunk.length > 0) {
      chunks.push(chunk);
    }
    
    currentIndex = endIndex - overlap;
    if (currentIndex >= text.length || chunkSize <= overlap) {
      break;
    }
  }
  
  return chunks;
}

/**
 * Procesa un archivo CSV y genera fragmentos agrupados por registros (filas) para preservar su estructura tabular
 */
function chunkCsvText(csvText: string, rowsPerChunk: number = 5): string[] {
  const lines = csvText.split('\n').filter(line => line.trim().length > 0);
  if (lines.length === 0) return [];
  
  const header = lines[0]; // Extraer el encabezado del CSV
  const dataLines = lines.slice(1);
  const chunks: string[] = [];
  
  for (let i = 0; i < dataLines.length; i += rowsPerChunk) {
    const chunkLines = dataLines.slice(i, i + rowsPerChunk);
    // Agrupar filas incluyendo el encabezado al inicio de cada chunk para dar contexto al modelo
    const chunk = [header, ...chunkLines].join('\n');
    chunks.push(chunk);
  }
  
  return chunks;
}

/**
 * Determina la categoría del documento según su nombre de archivo
 */
function getDocumentCategory(fileName: string): string {
  const lowerName = fileName.toLowerCase();
  if (lowerName.includes('entorno') || lowerName.includes('configuracion')) {
    return 'Entorno';
  }
  if (lowerName.includes('estilo') || lowerName.includes('practicas')) {
    return 'Estilo';
  }
  if (lowerName.includes('modulo') || lowerName.includes('arquitectura')) {
    return 'Arquitectura';
  }
  return 'General';
}

/**
 * Genera el embedding de un fragmento de texto usando el modelo de embeddings de Gemini
 */
async function generateEmbedding(text: string): Promise<number[]> {
  try {
    const response = await ai.models.embedContent({
      model: 'text-embedding-004',
      contents: text,
    });
    
    if (response.embedding?.values) {
      return response.embedding.values;
    }
    throw new Error('No se recibieron valores de embedding desde la API de Gemini.');
  } catch (error) {
    console.error('Error al llamar a la API de embeddings de Gemini:', error);
    throw error;
  }
}

/**
 * Pipeline principal de ingesta de documentos locales
 */
async function startIngestion() {
  console.log('Iniciando pipeline de ingesta de documentos RAG...');
  
  const kbDir = path.join(__dirname, '..', '..', 'knowledge-base');
  
  if (!fs.existsSync(kbDir)) {
    console.error(`El directorio de base de conocimientos no existe: ${kbDir}`);
    process.exit(1);
  }
  
  const files = fs.readdirSync(kbDir);
  console.log(`Archivos encontrados en la base de conocimientos: ${files.join(', ')}`);
  
  // Limpiar chunks anteriores para evitar duplicados en la ingesta inicial
  try {
    console.log('Limpiando base de datos de fragmentos anteriores...');
    await dbQuery('DELETE FROM document_chunks');
  } catch (err) {
    console.error('No se pudo limpiar la base de datos (asegúrate de correr primero las migraciones):', err);
    process.exit(1);
  }

  for (const file of files) {
    const filePath = path.join(kbDir, file);
    const category = getDocumentCategory(file);
    
    console.log(`\nProcesando archivo: "${file}" [Categoría: ${category}]`);
    
    try {
      // 1. Extraer texto según formato
      const fullText = await extractTextFromFile(filePath);
      
      // 2. Fragmentar texto según el formato (CSV recibe un chunking diferente)
      let chunks: string[] = [];
      const ext = path.extname(file).toLowerCase();
      if (ext === '.csv') {
        chunks = chunkCsvText(fullText, 4); // Agrupar de 4 en 4 filas con encabezado
      } else {
        chunks = chunkText(fullText, 800, 120); // Trozos estándar para Markdown/texto
      }
      
      console.log(`Archivo fragmentado en ${chunks.length} partes.`);
      
      // 3. Generar embeddings y guardar en base de datos
      for (let i = 0; i < chunks.length; i++) {
        const chunkContent = chunks[i];
        console.log(`Generando embedding e insertando fragmento ${i + 1}/${chunks.length}...`);
        
        // Obtener el vector embedding
        const vector = await generateEmbedding(chunkContent);
        
        // Convertir el array numérico de JS a formato vector de PostgreSQL: '[0.123, -0.456, ...]'
        const dbVectorFormat = `[${vector.join(',')}]`;
        
        // Insertar en la base de datos
        await dbQuery(
          `INSERT INTO document_chunks (documento_nombre, categoria, contenido, embedding)
           VALUES ($1, $2, $3, $4)`,
          [file, category, chunkContent, dbVectorFormat]
        );
      }
      
      console.log(`¡Archivo "${file}" indexado exitosamente!`);
    } catch (err) {
      console.error(`Error crítico procesando el archivo "${file}":`, err);
    }
  }
  
  console.log('\n=========================================');
  console.log('¡Pipeline de ingesta RAG finalizado con éxito!');
  console.log('Todos los documentos se han procesado y guardado.');
  console.log('=========================================');
  
  // Finalizar pool de base de datos
  await dbPool.end();
}

// Ejecutar si se llama directamente desde node/ts-node
if (require.main === module) {
  startIngestion();
}
