import express from 'express';
import cors from 'cors';
import * as dotenv from 'dotenv';
import { runAgentConversation } from './agent/orchestrator';

dotenv.config();

const app = express();
const PORT = process.env.PORT ? parseInt(process.env.PORT) : 3000;

// Middlewares estándar
app.use(cors());
app.use(express.json());

// Endpoint de Diagnóstico y Salud
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development'
  });
});

// Endpoint principal del Chat del Agente (RAG)
app.post('/api/chat', async (req, res, next) => {
  const { message, userId, chatId, categoria } = req.body;

  // Validación básica de parámetros
  if (!message || typeof message !== 'string' || message.trim().length === 0) {
    res.status(400).json({ error: 'El parámetro "message" es obligatorio.' });
    return;
  }

  // Generar un ID de usuario de prueba si no se proporciona
  const activeUserId = userId || '00000000-0000-0000-0000-000000000000';

  try {
    console.log(`[API] Recibido mensaje de usuario. User: ${activeUserId} | Chat: ${chatId || 'nuevo'} | Filtro: ${categoria || 'ninguno'}`);
    
    const result = await runAgentConversation(activeUserId, message, chatId, categoria);
    
    res.status(200).json({
      success: true,
      data: {
        reply: result.reply,
        chatId: result.chatId
      }
    });
  } catch (error) {
    console.error('[API] Error crítico procesando petición de chat:', error);
    next(error);
  }
});

// Middleware global de control de errores
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  res.status(500).json({
    success: false,
    error: 'Ocurrió un error interno en el servidor Express.'
  });
});

// Levantar el servidor
app.listen(PORT, '0.0.0.0', () => {
  console.log(`\n=========================================`);
  console.log(`🚀 Servidor backend Express levantado con éxito.`);
  console.log(`📍 Escuchando en: http://localhost:${PORT}`);
  console.log(`=========================================\n`);
});
export default app;
