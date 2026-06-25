import { useState, useEffect, useRef } from 'react';

interface Reference {
  documento: string;
  ubicacion: string;
  responsable: string;
  actualizado: string;
}

interface Message {
  id: string;
  role: 'user' | 'model';
  content: string;
  timestamp: Date;
  feedback: 'like' | 'dislike' | null;
  references: Reference[];
}

// URL base de la API backend (Vite soporta import.meta.env)
const API_URL = 'http://localhost:3000/api/chat';

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [chatId, setChatId] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string>('Todos');
  const [isLoading, setIsLoading] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 1. Cargar la sesión guardada desde LocalStorage en el arranque
  useEffect(() => {
    const savedChatId = localStorage.getItem('alura_agent_chat_id');
    const savedMessages = localStorage.getItem('alura_agent_messages');
    
    if (savedChatId) {
      setChatId(savedChatId);
    }
    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages);
        // Convertir strings de fechas de vuelta a objetos Date
        const messagesWithDates = parsed.map((m: any) => ({
          ...m,
          timestamp: new Date(m.timestamp)
        }));
        setMessages(messagesWithDates);
      } catch (err) {
        console.error('Error al cargar mensajes guardados:', err);
      }
    } else {
      // Mensaje de bienvenida inicial
      setMessages([
        {
          id: 'welcome',
          role: 'model',
          content: '¡Hola! Soy el **Agente Alura**, tu mentor de código y asistente de onboarding corporativo. 🤖\n\nPuedo responder tus dudas técnicas sobre la base de conocimientos de desarrollo de la empresa (instalación del entorno, guías de estilo, estructura de módulos, etc.). ¿En qué puedo ayudarte hoy?',
          timestamp: new Date(),
          feedback: null,
          references: []
        }
      ]);
    }
  }, []);

  // 2. Persistir mensajes en LocalStorage cada vez que cambien
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('alura_agent_messages', JSON.stringify(messages));
    }
  }, [messages]);

  // 3. Auto-scroll al final del chat al recibir mensajes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  /**
   * Parsea el texto del backend para extraer la sección de "Referencias Utilizadas"
   */
  const parseReferencesAndText = (text: string): { cleanText: string; references: Reference[] } => {
    const referenceHeaderIndex = text.indexOf('### Referencias Utilizadas');
    
    if (referenceHeaderIndex === -1) {
      return { cleanText: text, references: [] };
    }
    
    const cleanText = text.substring(0, referenceHeaderIndex).trim();
    const referencesText = text.substring(referenceHeaderIndex);
    
    // Procesar cada línea de referencia
    const lines = referencesText.split('\n');
    const references: Reference[] = [];
    
    // Regex: - *Documento*: (.*?) | *Ubicación*: (.*?) | *Responsable*: (.*?) | *Actualizado*: (.*)
    const regex = /-\s*\*Documento\*:\s*(.*?)\s*\|\s*\*Ubicación\*:\s*(.*?)\s*\|\s*\*Responsable\*:\s*(.*?)\s*\|\s*\*Actualizado\*:\s*(.*)/;
    
    lines.forEach(line => {
      const match = line.match(regex);
      if (match) {
        references.push({
          documento: match[1].trim(),
          ubicacion: match[2].trim(),
          responsable: match[3].trim(),
          actualizado: match[4].trim()
        });
      }
    });
    
    return { cleanText, references };
  };

  /**
   * Envía la consulta al servidor Express backend
   */
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;

    const userMsgText = inputText;
    setInputText('');
    
    // 1. Agregar el mensaje del usuario de forma local
    const newUserMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: userMsgText,
      timestamp: new Date(),
      feedback: null,
      references: []
    };
    
    setMessages(prev => [...prev, newUserMessage]);
    setIsLoading(true);

    try {
      // 2. Realizar petición POST al backend
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsgText,
          chatId: chatId, // Enviar ID actual si existe
          userId: '00000000-0000-0000-0000-000000000000', // Mock UUID
          categoria: categoryFilter === 'Todos' ? undefined : categoryFilter
        })
      });

      if (!response.ok) {
        throw new Error('Fallo al conectar con el servidor backend.');
      }

      const resJson = await response.json();
      
      if (resJson.success && resJson.data) {
        const { reply, chatId: returnedChatId } = resJson.data;
        
        // Guardar el ID de chat retornado
        if (returnedChatId && returnedChatId !== chatId) {
          setChatId(returnedChatId);
          localStorage.setItem('alura_agent_chat_id', returnedChatId);
        }

        // Extraer texto limpio y citas estructuradas
        const { cleanText, references } = parseReferencesAndText(reply);

        const newBotMessage: Message = {
          id: `bot-${Date.now()}`,
          role: 'model',
          content: cleanText,
          timestamp: new Date(),
          feedback: null,
          references
        };

        setMessages(prev => [...prev, newBotMessage]);
      } else {
        throw new Error(resJson.error || 'Respuesta fallida del backend');
      }
    } catch (err) {
      console.error(err);
      const errorBotMessage: Message = {
        id: `err-${Date.now()}`,
        role: 'model',
        content: '⚠️ Ocurrió un error al intentar conectarse con el servidor backend local o con la API de Gemini.',
        timestamp: new Date(),
        feedback: null,
        references: []
      };
      setMessages(prev => [...prev, errorBotMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Resetea el chat e inicializa una sesión vacía
   */
  const handleNewChat = () => {
    localStorage.removeItem('alura_agent_chat_id');
    localStorage.removeItem('alura_agent_messages');
    setChatId(null);
    setMessages([
      {
        id: 'welcome',
        role: 'model',
        content: '¡Hola! Soy el **Agente Alura**, tu mentor de código y asistente de onboarding corporativo. 🤖\n\nPuedo responder tus dudas técnicas sobre la base de conocimientos de desarrollo de la empresa (instalación del entorno, guías de estilo, estructura de módulos, etc.). ¿En qué puedo ayudarte hoy?',
        timestamp: new Date(),
        feedback: null,
        references: []
      }
    ]);
  };

  /**
   * Registra el feedback del colaborador (Me gusta / No me gusta)
   */
  const handleFeedback = (messageId: string, type: 'like' | 'dislike') => {
    setMessages(prev => prev.map(msg => {
      if (msg.id === messageId) {
        return {
          ...msg,
          // Si hace clic en el mismo feedback activo, lo apaga; si no, lo activa
          feedback: msg.feedback === type ? null : type
        };
      }
      return msg;
    }));
  };

  return (
    <div className="app-container">
      {/* 1. Panel Lateral (Sidebar) */}
      <aside className="sidebar">
        <div className="brand-section">
          <span className="brand-icon">🤖</span>
          <h1 className="brand-title">Agente Alura</h1>
        </div>

        <div className="sidebar-label">Información de Sesión</div>
        <div className="sidebar-card">
          <p>
            <strong>Estado:</strong> Conectado a OCI<br />
            <strong>Sesión:</strong> {chatId ? chatId.substring(0, 8) + '...' : 'Nuevo Chat'}<br />
            <strong>RAG Data:</strong> Local/GitHub
          </p>
        </div>

        <div className="sidebar-label">Acciones</div>
        <button className="btn-new-chat" onClick={handleNewChat}>
          <span>💬</span> Nuevo Chat
        </button>

        <div style={{ marginTop: 'auto' }}>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'center' }}>
            Desafío Alura Agentes v1.0.0
          </p>
        </div>
      </aside>

      {/* 2. Panel de Chat Principal */}
      <main className="chat-panel">
        
        {/* Encabezado Superior (Header) */}
        <header className="chat-header">
          <div className="agent-identity">
            <div className="agent-avatar">🤖</div>
            <div className="agent-status-wrapper">
              <span className="agent-name">Mentor de Onboarding</span>
              <span className="agent-badge">Disponible en la nube</span>
            </div>
          </div>

          {/* Filtro de Categorías */}
          <div className="category-filter-bar">
            {['Todos', 'Entorno', 'Estilo', 'Arquitectura'].map(cat => (
              <button
                key={cat}
                className={`filter-btn ${categoryFilter === cat ? 'active' : ''}`}
                onClick={() => setCategoryFilter(cat)}
              >
                {cat}
              </button>
            ))}
          </div>
        </header>

        {/* Área de Mensajes (Scrollable) */}
        <div className="messages-container">
          {messages.map(msg => {
            const isBot = msg.role === 'model';
            return (
              <div key={msg.id} className={`message-row ${isBot ? 'bot' : 'user'}`}>
                <div className="message-bubble">
                  <div className="message-header">
                    {isBot ? '🤖 MENTOR COGNITIVO' : '👨‍💻 COLABORADOR'}
                  </div>
                  <div className="message-text">
                    {msg.content}
                  </div>

                  {/* Renderizado de Referencias Citas si existen */}
                  {isBot && msg.references.length > 0 && (
                    <div className="references-section">
                      <div className="references-title">
                        <span>📄</span> Fuentes y Documentos Citados:
                      </div>
                      <div className="references-grid">
                        {msg.references.map((ref, idx) => (
                          <div key={idx} className="reference-pill">
                            <strong>Archivo:</strong> {ref.documento} | 
                            <strong> Ubicación:</strong> {ref.ubicacion} <br />
                            <strong>Responsable:</strong> {ref.responsable} | 
                            <strong> Actualización:</strong> {ref.actualizado}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Botones de Feedback (Likes) para respuestas del Bot */}
                  {isBot && msg.id !== 'welcome' && (
                    <div className="feedback-actions">
                      <button
                        className={`feedback-btn like ${msg.feedback === 'like' ? 'active' : ''}`}
                        onClick={() => handleFeedback(msg.id, 'like')}
                        title="Respuesta Útil"
                      >
                        👍 {msg.feedback === 'like' ? 'Útil' : ''}
                      </button>
                      <button
                        className={`feedback-btn dislike ${msg.feedback === 'dislike' ? 'active' : ''}`}
                        onClick={() => handleFeedback(msg.id, 'dislike')}
                        title="Respuesta Irrelevante o Incorrecta"
                      >
                        👎 {msg.feedback === 'dislike' ? 'Incompleto' : ''}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {/* Typing Indicator cuando el bot está pensando */}
          {isLoading && (
            <div className="message-row bot">
              <div className="message-bubble" style={{ padding: '12px' }}>
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input de Mensaje inferior */}
        <div className="chat-input-area">
          <form onSubmit={handleSendMessage} className="input-container">
            <input
              type="text"
              className="chat-input"
              placeholder="Haz una pregunta técnica sobre guías de estilo, instalación o arquitectura..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              disabled={isLoading}
            />
            <button
              type="submit"
              className="btn-send"
              disabled={isLoading || !inputText.trim()}
            >
              🚀
            </button>
          </form>
        </div>

      </main>
    </div>
  );
}
