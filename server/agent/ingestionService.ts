import * as fs from 'fs';
import * as path from 'path';
import * as dotenv from 'dotenv';
import { GoogleGenAI } from '@google/genai';
import { dbQuery, dbPool } from '../db/client';
import { parseDocumentToSegments, DocumentSegment, cleanTextContent } from './documentParser';

dotenv.config();

const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
if (!GEMINI_API_KEY) {
  console.error('Error: La variable de entorno GEMINI_API_KEY no está configurada.');
  process.exit(1);
}

// Inicializar el SDK de Google Gen AI
const ai = new GoogleGenAI({ apiKey: GEMINI_API_KEY });

/**
 * En caso de que un segmento extraído (por ejemplo, una página PDF muy larga)
 * exceda el límite de caracteres sugerido para un embedding de calidad,
 * este helper subdivide el segmento manteniendo su metadato de ubicación.
 */
function subChunkSegment(text: string, maxChunkSize: number = 1000, overlap: number = 150): string[] {
  if (text.length <= maxChunkSize) {
    return [text];
  }
  
  const subChunks: string[] = [];
  let currentIndex = 0;
  
  while (currentIndex < text.length) {
    let endIndex = currentIndex + maxChunkSize;
    
    if (endIndex < text.length) {
      const lastSpace = text.lastIndexOf(' ', endIndex);
      if (lastSpace > currentIndex) {
        endIndex = lastSpace;
      }
    }
    
    const subChunk = text.substring(currentIndex, endIndex).trim();
    if (subChunk.length > 0) {
      subChunks.push(subChunk);
    }
    
    currentIndex = endIndex - overlap;
    if (currentIndex >= text.length || maxChunkSize <= overlap) {
      break;
    }
  }
  
  return subChunks;
}

/**
 * Determina la categoría del documento según su nombre de archivo
 */
function getDocumentCategory(fileName: string): string {
  const lowerName = fileName.toLowerCase();
  if (
    lowerName.includes('entorno') || 
    lowerName.includes('configuracion') || 
    lowerName.includes('onboarding') || 
    lowerName.includes('incidentes')
  ) {
    return 'Entorno';
  }
  if (
    lowerName.includes('estilo') || 
    lowerName.includes('practicas') || 
    lowerName.includes('frontend') || 
    lowerName.includes('backend')
  ) {
    return 'Estilo';
  }
  if (
    lowerName.includes('modulo') || 
    lowerName.includes('arquitectura') || 
    lowerName.includes('dominios')
  ) {
    return 'Arquitectura';
  }
  return 'General';
}

/**
 * Asigna el responsable del documento (ownership) según su categoría
 */
function getDocumentOwner(category: string): string {
  switch (category) {
    case 'Entorno':
      return 'DevOps Lead / Tech Lead';
    case 'Estilo':
      return 'Frontend & Backend Leads';
    case 'Arquitectura':
      return 'Software Architect';
    default:
      return 'Comité de Documentación Corporativa';
  }
}

/**
 * Llama a la API de Gemini para generar el embedding de un fragmento de texto
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
    throw new Error('La respuesta de embeddings de Gemini está vacía.');
  } catch (error) {
    console.error('Fallo de llamada a la API de embeddings de Gemini:', error);
    throw error;
  }
}

/**
 * Pipeline principal de ingesta avanzada de documentos RAG (Etapa 2)
 */
async function startIngestion() {
  console.log('Iniciando pipeline avanzado de ingesta y extracción (Etapa 2)...');
  
  const kbDir = path.join(__dirname, '..', '..', 'knowledge-base');
  
  if (!fs.existsSync(kbDir)) {
    console.error(`El directorio de base de conocimientos no existe: ${kbDir}`);
    process.exit(1);
  }
  
  const files = fs.readdirSync(kbDir);
  console.log(`Archivos detectados en knowledge-base: ${files.join(', ')}`);
  
  // Limpiar chunks anteriores
  try {
    console.log('Limpiando base de datos de fragmentos anteriores...');
    await dbQuery('DELETE FROM document_chunks');
  } catch (err) {
    console.error('No se pudo limpiar la base de datos (corre primero las migraciones):', err);
    process.exit(1);
  }

  for (const file of files) {
    const filePath = path.join(kbDir, file);
    const category = getDocumentCategory(file);
    const owner = getDocumentOwner(category);
    
    // Obtener fecha de última modificación del archivo
    const fileStats = fs.statSync(filePath);
    const lastModified = fileStats.mtime; // Date object
    
    console.log(`\nProcesando archivo: "${file}"`);
    console.log(`- Categoría: ${category}`);
    console.log(`- Responsable: ${owner}`);
    console.log(`- Última Actualización: ${lastModified.toISOString()}`);
    
    try {
      // 1. Extraer segmentos estructurados con ubicación usando documentParser.ts
      const segments: DocumentSegment[] = await parseDocumentToSegments(filePath);
      
      console.log(`Documento dividido originalmente en ${segments.length} segmentos estructurales.`);
      
      let chunkCounter = 0;
      
      // 2. Procesar cada segmento
      for (const segment of segments) {
        // Limpieza de ruido del segmento
        const cleanContent = cleanTextContent(segment.content);
        if (cleanContent.length === 0) continue;
        
        // Sub-chunking en caso de que exceda el tamaño sugerido
        const subChunks = subChunkSegment(cleanContent, 1000, 150);
        
        for (let j = 0; j < subChunks.length; j++) {
          chunkCounter++;
          const finalChunkText = subChunks[j];
          
          // Crear un indicador de ubicación más específico si se subdividió
          const finalLocation = subChunks.length > 1 
            ? `${segment.location} (Parte ${j + 1}/${subChunks.length})`
            : segment.location;
            
          console.log(`Indexando fragmento ${chunkCounter} (${finalLocation})...`);
          
          // 3. Generar embedding vectorial
          const vector = await generateEmbedding(finalChunkText);
          const dbVectorFormat = `[${vector.join(',')}]`;
          
          // 4. Guardar en base de datos con todos los metadatos de la Etapa 2
          await dbQuery(
            `INSERT INTO document_chunks 
             (documento_nombre, categoria, contenido, ubicacion_exacta, autor_responsable, ultima_actualizacion, embedding)
             VALUES ($1, $2, $3, $4, $5, $6, $7)`,
            [file, category, finalChunkText, finalLocation, owner, lastModified, dbVectorFormat]
          );
        }
      }
      
      console.log(`¡Archivo "${file}" indexado exitosamente con ${chunkCounter} fragmentos de vectores!`);
    } catch (err) {
      console.error(`Error crítico procesando el archivo "${file}":`, err);
    }
  }
  
  console.log('\n=========================================');
  console.log('¡Pipeline de ingesta avanzada (Etapa 2) finalizado con éxito!');
  console.log('Todos los archivos y sus metadatos se guardaron en la base de datos.');
  console.log('=========================================');
  
  await dbPool.end();
}

// Ejecutar si se llama directamente
if (require.main === module) {
  startIngestion();
}
