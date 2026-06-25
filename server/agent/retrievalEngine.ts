import * as dotenv from 'dotenv';
import { GoogleGenAI, Type } from '@google/genai';
import { dbQuery } from '../db/client';

dotenv.config();

const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
if (!GEMINI_API_KEY) {
  throw new Error('La variable de entorno GEMINI_API_KEY no está configurada.');
}

const ai = new GoogleGenAI({ apiKey: GEMINI_API_KEY });

export interface RetrievedChunk {
  id: string;
  documento_nombre: string;
  categoria: string;
  contenido: string;
  ubicacion_exacta: string;
  autor_responsable: string;
  ultima_actualizacion: Date;
  similitud: number;
  score?: number; // Para el Reranker
}

/**
 * Genera el vector embedding de la pregunta del usuario
 */
async function generateQueryEmbedding(query: string): Promise<number[]> {
  try {
    const response = await ai.models.embedContent({
      model: 'text-embedding-004',
      contents: query,
    });
    
    if (response.embedding?.values) {
      return response.embedding.values;
    }
    throw new Error('Fallo al recuperar embeddings para la consulta del usuario.');
  } catch (error) {
    console.error('Error al generar query embedding:', error);
    throw error;
  }
}

/**
 * Realiza el Reranking (Reclasificación) de los fragmentos usando Gemini Flash.
 * Evalúa la pertinencia específica de cada fragmento respecto a la consulta en una escala de 0 a 10.
 */
async function rerankCandidates(query: string, candidates: RetrievedChunk[]): Promise<RetrievedChunk[]> {
  if (candidates.length === 0) return [];
  
  // Si solo hay un candidato, no es necesario re-clasificar
  if (candidates.length === 1) {
    candidates[0].score = 10;
    return candidates;
  }

  console.log(`[Reranker] Evaluando relevancia de ${candidates.length} candidatos con Gemini...`);

  // Construir prompt estructurado para la evaluación
  const formattedCandidates = candidates.map((c, i) => 
    `--- FRAGMENTO ID: ${i} (Categoría: ${c.categoria} | Ubicación: ${c.ubicacion_exacta}) ---\n${c.contenido}`
  ).join('\n\n');

  const prompt = `Actúas como un clasificador de relevancia técnica.
Evalúa la utilidad de los siguientes fragmentos para responder con precisión a la pregunta del colaborador.
Pregunta del Colaborador: "${query}"

Fragmentos de Documentos:
${formattedCandidates}

Asigna a cada FRAGMENTO ID una puntuación entera del 0 al 10 (donde 0 es completamente irrelevante y 10 responde directamente a la pregunta con exactitud).`;

  try {
    // Solicitar salida JSON estructurada
    const response = await ai.models.generateContent({
      model: 'gemini-3.5-flash',
      contents: prompt,
      config: {
        responseMimeType: 'application/json',
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            evaluaciones: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  index: { type: Type.INTEGER, description: 'ID del fragmento evaluado' },
                  score: { type: Type.INTEGER, description: 'Puntaje de relevancia de 0 a 10' },
                  motivo: { type: Type.STRING, description: 'Breve explicación de la relevancia' }
                },
                required: ['index', 'score']
              }
            }
          },
          required: ['evaluaciones']
        }
      }
    });

    const responseText = response.text;
    if (!responseText) {
      console.warn('[Reranker] Respuesta de IA vacía en el Reranking. Retornando candidatos por orden de vector original.');
      return candidates;
    }

    const result = JSON.parse(responseText);
    const evaluaciones: { index: number; score: number }[] = result.evaluaciones || [];

    // Mapear los scores calculados a los candidatos originales
    evaluaciones.forEach((evalItem) => {
      const idx = evalItem.index;
      if (idx >= 0 && idx < candidates.length) {
        candidates[idx].score = evalItem.score;
      }
    });

    // Rellenar con 0 si algún candidato no fue calificado por alguna anomalía
    candidates.forEach(c => {
      if (c.score === undefined) c.score = 0;
    });

    // Ordenar de mayor a menor puntuación y filtrar los que tengan baja relevancia (menor a 5/10)
    const sortedAndFiltered = candidates
      .sort((a, b) => (b.score || 0) - (a.score || 0))
      .filter(c => (c.score || 0) >= 5);
      
    console.log(`[Reranker] Reranking completado. Candidatos filtrados y ordenados. Mejor puntaje: ${sortedAndFiltered[0]?.score}/10`);
    return sortedAndFiltered;
  } catch (error) {
    console.error('Error durante el proceso de Reranking. Usando fallback de orden vectorial:', error);
    // Fallback: Retornar los candidatos por orden de distancia de coseno original
    return candidates;
  }
}

/**
 * Ensambla los fragmentos ganadores en un bloque de texto contextual
 * formateado de forma estructurada con sus metadatos de origen para el LLM.
 */
function assembleContextBlock(chunks: RetrievedChunk[]): string {
  if (chunks.length === 0) {
    return 'No se encontraron documentos relevantes en la base de conocimientos.';
  }

  return chunks.map((chunk, i) => {
    const header = `[FUENTE DE CONOCIMIENTO #${i + 1}]
- Archivo: ${chunk.documento_nombre}
- Categoría: ${chunk.categoria}
- Ubicación Exacta: ${chunk.ubicacion_exacta}
- Responsable: ${chunk.autor_responsable}
- Última Actualización: ${chunk.ultima_actualizacion.toISOString()}`;

    return `${header}\nContenido:\n"""\n${chunk.contenido}\n"""`;
  }).join('\n\n=========================================\n\n');
}

/**
 * Función principal de la Capa de Recuperación (RAG)
 * @param query La pregunta técnica del desarrollador.
 * @param categoryFilter Filtro opcional por categoría de metadato.
 * @param limitCandidates Número de candidatos iniciales a recuperar para vector (default 10).
 * @param limitFinal Número final de fragmentos a pasar al LLM tras reranking (default 3).
 */
export async function retrieveRelevantContext(
  query: string,
  categoryFilter?: string,
  limitCandidates: number = 10,
  limitFinal: number = 3
): Promise<string> {
  
  // 1. Convertir pregunta del colaborador en vector embedding
  const queryVector = await generateQueryEmbedding(query);
  const vectorString = `[${queryVector.join(',')}]`;
  
  let dbResult;
  
  // 2. Búsqueda semántica usando distancia por coseno (<=>) en pgvector
  // Nota: (1 - (embedding <=> queryVector)) entrega el Score de Similitud del Coseno
  if (categoryFilter) {
    dbResult = await dbQuery(
      `SELECT id, documento_nombre, categoria, contenido, ubicacion_exacta, autor_responsable, ultima_actualizacion,
       1 - (embedding <=> $1) AS similitud
       FROM document_chunks
       WHERE categoria = $2
       ORDER BY embedding <=> $1
       LIMIT $3`,
      [vectorString, categoryFilter, limitCandidates]
    );
  } else {
    dbResult = await dbQuery(
      `SELECT id, documento_nombre, categoria, contenido, ubicacion_exacta, autor_responsable, ultima_actualizacion,
       1 - (embedding <=> $1) AS similitud
       FROM document_chunks
       ORDER BY embedding <=> $1
       LIMIT $2`,
      [vectorString, limitCandidates]
    );
  }

  const candidates: RetrievedChunk[] = dbResult.rows.map(row => ({
    id: row.id,
    documento_nombre: row.documento_nombre,
    categoria: row.categoria,
    contenido: row.contenido,
    ubicacion_exacta: row.ubicacion_exacta,
    autor_responsable: row.autor_responsable,
    ultima_actualizacion: new Date(row.ultima_actualizacion),
    similitud: parseFloat(row.similitud)
  }));

  if (candidates.length === 0) {
    return '';
  }

  // 3. Reranking (Reclasificación) usando Gemini Flash
  const rerankedChunks = await rerankCandidates(query, candidates);

  // 4. Retener solo los N mejores fragmentos finales
  const finalChunks = rerankedChunks.slice(0, limitFinal);

  // 5. Ensamblar y retornar el contexto formateado
  return assembleContextBlock(finalChunks);
}
