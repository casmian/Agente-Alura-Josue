import * as dotenv from 'dotenv';
import { GoogleGenAI } from '@google/genai';
import { dbQuery } from '../db/client';
import { retrieveRelevantContext } from './retrievalEngine';

dotenv.config();

const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
if (!GEMINI_API_KEY) {
  throw new Error('La variable de entorno GEMINI_API_KEY no está configurada.');
}

const ai = new GoogleGenAI({ apiKey: GEMINI_API_KEY });

interface AgentResponse {
  reply: string;
  chatId: string;
}

/**
 * Recupera el historial de chat guardado en PostgreSQL
 */
async function fetchChatHistory(chatId: string): Promise<{ role: string; content: string }[]> {
  try {
    const res = await dbQuery(
      `SELECT role, content 
       FROM messages 
       WHERE chat_id = $1 
       ORDER BY created_at ASC`,
      [chatId]
    );
    return res.rows.map(row => ({
      role: row.role,
      content: row.content
    }));
  } catch (err) {
    console.error('Error al recuperar el historial de chat:', err);
    return []; // Retornar array vacío en caso de fallo
  }
}

/**
 * Guarda un mensaje individual en la base de datos PostgreSQL
 */
async function saveMessage(chatId: string, role: 'user' | 'model', content: string): Promise<void> {
  try {
    await dbQuery(
      `INSERT INTO messages (chat_id, role, content) 
       VALUES ($1, $2, $3)`,
      [chatId, role, content]
    );
  } catch (err) {
    console.error('Error al persistir mensaje en base de datos:', err);
  }
}

/**
 * Crea una nueva sesión de chat en la base de datos
 */
async function createNewChatSession(userId: string, title: string = 'Nueva Consulta'): Promise<string> {
  try {
    // Si no hay usuarios en la BD, creamos un usuario por defecto
    const userCheck = await dbQuery('SELECT id FROM users LIMIT 1');
    let dbUserId = userId;
    
    if (userCheck.rows.length === 0) {
      console.log('No se encontraron usuarios. Creando usuario por defecto...');
      const newUser = await dbQuery(
        `INSERT INTO users (nombre, email) 
         VALUES ('Colaborador Alura', 'colaborador@alura.edu') 
         RETURNING id`
      );
      dbUserId = newUser.rows[0].id;
    }

    const res = await dbQuery(
      `INSERT INTO chats (user_id, titulo) 
       VALUES ($1, $2) 
       RETURNING id`,
      [dbUserId, title]
    );
    return res.rows[0].id;
  } catch (err) {
    console.error('Error al crear nueva sesión de chat:', err);
    throw err;
  }
}

/**
 * Orquestador de la conversación (Stage 5)
 * Coordina RAG, historial persistente, generación de respuestas sin alucinaciones y citación de fuentes.
 * 
 * @param userId ID del usuario
 * @param userMessage Pregunta del colaborador
 * @param chatId ID opcional del chat existente
 * @param categoryFilter Filtro opcional de categoría
 */
export async function runAgentConversation(
  userId: string,
  userMessage: string,
  chatId?: string,
  categoryFilter?: string
): Promise<AgentResponse> {
  
  // 1. Obtener o inicializar el ID del chat
  let activeChatId = chatId;
  if (!activeChatId) {
    // Crear título corto basado en los primeros caracteres de la pregunta
    const title = userMessage.length > 30 ? `${userMessage.substring(0, 30)}...` : userMessage;
    activeChatId = await createNewChatSession(userId, title);
  }

  // 2. Guardar el mensaje del usuario en PostgreSQL
  await saveMessage(activeChatId, 'user', userMessage);

  // 3. Recuperar historial persistente
  const history = await fetchChatHistory(activeChatId);

  // 4. Recuperar contexto RAG relevante
  const context = await retrieveRelevantContext(userMessage, categoryFilter);

  // 5. Control de alucinaciones: si la base de datos RAG no retornó nada, ejecutamos el Fallback de inmediato
  if (!context || context.trim() === '') {
    const fallbackReply = 'Lo siento, no encontré esta información en los documentos corporativos disponibles.\n\nPor favor, ponte en contacto con el **Comité de Documentación Corporativa** o con el **Líder Técnico** para resolver esta inquietud específica.';
    await saveMessage(activeChatId, 'model', fallbackReply);
    return { reply: fallbackReply, chatId: activeChatId };
  }

  // 6. Configurar el System Instruction (Guía de comportamiento estricto)
  const systemInstruction = `Eres el Agente Alura, un asistente inteligente corporativo y mentor de código.
Tu objetivo es responder las dudas de los colaboradores basándote exclusivamente en el contexto que se te proporciona.

REGLAS DE GENERACIÓN Y CONTROL DE ALUCINACIONES:
1. Responde ÚNICAMENTE con base en los fragmentos de conocimiento proveídos en la sección [FUENTE DE CONOCIMIENTO]. No uses conocimiento general ni supongas información.
2. Si la información necesaria para responder la consulta no está presente en la [FUENTE DE CONOCIMIENTO] provista, di textualmente: "Lo siento, no encontré esta información en los documentos disponibles." y a continuación indica al usuario que contacte al responsable de esa categoría de acuerdo a los datos de la fuente.
3. Sé conciso, claro y profesional. Utiliza formato markdown para organizar las explicaciones técnicas y el código.
4. Al final de tu respuesta, debes incluir una sección titulada "### Referencias Utilizadas" listando de forma ordenada cada archivo, sección/página y responsable citado.
   Formato de referencia:
   - *Documento*: [Nombre del archivo] | *Ubicación*: [Ubicación exacta] | *Responsable*: [Autor responsable] | *Actualizado*: [Fecha de modificación]`;

  // 7. Preparar la entrada del modelo compilando el historial y el contexto
  const formattedPrompt = `Pregunta actual del colaborador: "${userMessage}"

[FUENTE DE CONOCIMIENTO]
${context}

Recuerda responder solo usando esta fuente y citar las referencias al final.`;

  try {
    // Convertir el historial al formato compatible con el SDK
    // El SDK de Google Gen AI para generateContent espera contents: string o Content[]
    // Para simplificar, pasamos el contexto actual e integramos el historial como parte de la conversación
    const chatContents = history.map(msg => ({
      role: msg.role,
      parts: [{ text: msg.content }]
    }));

    // Reemplazar la última entrada con nuestro prompt enriquecido con RAG
    if (chatContents.length > 0) {
      chatContents[chatContents.length - 1].parts = [{ text: formattedPrompt }];
    } else {
      chatContents.push({
        role: 'user',
        parts: [{ text: formattedPrompt }]
      });
    }

    // 8. Solicitar la respuesta a Gemini Flash
    const response = await ai.models.generateContent({
      model: 'gemini-3.5-flash',
      contents: chatContents,
      config: {
        systemInstruction: systemInstruction,
        temperature: 0.1 // Mantener temperatura baja para rigidez teórica
      }
    });

    const replyText = response.text || 'Lo siento, ocurrió una anomalía al procesar la respuesta.';

    // 9. Guardar respuesta del agente en la base de datos
    await saveMessage(activeChatId, 'model', replyText);

    return {
      reply: replyText,
      chatId: activeChatId
    };
  } catch (error) {
    console.error('Error al generar respuesta de conversación del agente:', error);
    const errorReply = 'Lo siento, ocurrió un error en la capa de procesamiento cognitivo de la IA.';
    return {
      reply: errorReply,
      chatId: activeChatId
    };
  }
}
