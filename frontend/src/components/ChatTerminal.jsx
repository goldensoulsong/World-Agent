import React, { useState, useRef, useEffect } from 'react';
import { marked } from 'marked';

function ChatTerminal({ sessionId, setAgentState, refreshSessions }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef(null);

  // Load initial messages for this session
  useEffect(() => {
    let isMounted = true;
    const loadSession = async () => {
      try {
        const res = await fetch(`/api/chats/${sessionId}`);
        if (res.ok) {
          const data = await res.json();
          if (isMounted && data.messages) {
            setMessages(data.messages);
          }
        } else {
          // New session or not found
          setMessages([]);
        }
      } catch (e) {
        console.error("Failed to load session", e);
      }
    };
    loadSession();
    return () => { isMounted = false; };
  }, [sessionId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Save to backend
  const saveSessionToBackend = async (msgs) => {
    if (msgs.length === 0) return;
    
    // Use first user message as title
    let title = "新对话";
    const firstUserMsg = msgs.find(m => m.role === 'user');
    if (firstUserMsg && firstUserMsg.content) {
      const contentStr = String(firstUserMsg.content);
      title = contentStr.substring(0, 15);
      if (contentStr.length > 15) title += "...";
    }

    try {
      // Strip internal streaming fields, persist only role + content
      const cleanMsgs = msgs
        .filter(m => m.role === 'user' || m.role === 'assistant' || m.role === 'error')
        .map(m => ({ role: m.role, content: m.content || '' }));

      await fetch(`/api/chats/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          updated_at: new Date().toISOString(),
          messages: cleanMsgs
        })
      });
      refreshSessions();
    } catch (e) {
      console.error("Failed to save chat to backend", e);
    }
  };

  const handleSubmit = async () => {
    if (!input.trim() || isProcessing) return;
    
    const userMsg = input.trim();
    setInput('');
    setIsProcessing(true);
    setAgentState('thinking');

    // Add user message
    let currentMsgs = [...messages, { role: 'user', content: userMsg }];
    setMessages(currentMsgs);
    
    // Save immediately so user message is persisted even if AI fails
    saveSessionToBackend(currentMsgs);

    // Prepare assistant message
    const msgId = Date.now();
    const newAiMsg = { 
      id: msgId,
      role: 'assistant', 
      thoughts: '', 
      actions: [], 
      content: '', 
      isStreaming: true 
    };
    currentMsgs = [...currentMsgs, newAiMsg];
    setMessages(currentMsgs);

    try {
      const getResponse = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMsg, session_id: sessionId })
      });

      const reader = getResponse.body.getReader();
      const decoder = new TextDecoder("utf-8");

      let finalAiMsg = { ...newAiMsg };
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        buffer = lines.pop(); // Keep the last incomplete line in the buffer
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.substring(6).trim();
            if (!dataStr) continue;
            
            try {
              const data = JSON.parse(dataStr);
              
              if (data.type === 'thought') {
                setAgentState('thinking');
                finalAiMsg.thoughts += data.content;
              } else if (data.type === 'action') {
                setAgentState('working');
                finalAiMsg.actions.push({ function: data.function, input: data.args });
              } else if (data.type === 'observation') {
                setAgentState('thinking');
              } else if (data.type === 'answer') {
                setAgentState('idle');
                finalAiMsg.content += data.content;
              }

              // Update state for rendering
              setMessages(prev => prev.map(m => m.id === msgId ? { ...finalAiMsg } : m));

            } catch (e) {
              console.error('JSON Parse Error in SSE:', e, dataStr);
            }
          }
        }
      }
      
      // Mark as done
      finalAiMsg.isStreaming = false;
      
      // Update state
      setMessages(prev => prev.map(m => m.id === msgId ? finalAiMsg : m));
      
      // Save the fully completed conversation
      const finalMsgs = currentMsgs.map(m => m.id === msgId ? finalAiMsg : m);
      saveSessionToBackend(finalMsgs);
      setAgentState('idle');
      setIsProcessing(false);

    } catch (error) {
      console.error(error);
      setMessages(prev => {
        const newArr = [...prev, { role: 'error', content: 'Connection failed.' }];
        saveSessionToBackend(newArr);
        return newArr;
      });
      setAgentState('idle');
      setIsProcessing(false);
    }
  };

  const renderMarkdown = (text) => {
    try {
      if (!text) return { __html: '' };
      const strText = typeof text === 'string' ? text : String(text);
      return { __html: marked.parse(strText) };
    } catch (e) {
      console.error('Markdown parse error:', e);
      return { __html: text };
    }
  };

  return (
    <div className="chat-container glass-panel">
      <div className="chat-messages" id="chat-content">
        <div className="message" style={{justifyContent: 'center', maxWidth: '100%'}}>
          <div style={{textAlign: 'center', padding: '20px 0'}}>
            <div style={{fontSize: '2rem', marginBottom: '8px'}}>✨</div>
            <h3 style={{fontFamily: 'var(--font-title)', fontSize: '1.2rem', fontWeight: 600}}>Nexus Core Online</h3>
            <p style={{fontSize: '0.8rem', color: 'var(--text-ink-muted)', marginTop: '4px'}}>Session: {sessionId}</p>
          </div>
        </div>
        
        {messages.map((msg, idx) => {
          if (msg.role === 'user') {
            return (
              <div key={idx} className="message user-message">
                <div className="avatar user-avatar">U</div>
                <div className="content">{msg.content}</div>
              </div>
            );
          } else if (msg.role === 'assistant') {
            return (
              <div key={msg.id || idx} className="message ai-message">
                <div className="avatar ai-avatar">AI</div>
                <div className="content" style={{ width: '100%' }}>
                  {/* Trace Box */}
                  {(msg.thoughts || msg.actions?.length > 0 || msg.isStreaming) && (
                    <details className="trace-details" open={msg.isStreaming}>
                      <summary className="trace-summary">
                        {msg.isStreaming ? <span className="dot"></span> : '✔️'} 
                        {msg.isStreaming ? ' Processing...' : ' Execution Complete (Click to expand)'}
                      </summary>
                      <div className="trace-box">
                        {msg.thoughts && <div className="trace-thought" style={{whiteSpace:'pre-wrap'}}>{msg.thoughts}</div>}
                        {msg.actions && Array.isArray(msg.actions) && msg.actions.map((act, i) => (
                          <div key={i} className="trace-action" style={{marginTop: '10px', color: 'var(--accent-blue)'}}>
                            <strong>🔧 Used Tool:</strong> {act.function}
                            <pre style={{background:'rgba(0,0,0,0.05)', padding:'5px', marginTop:'5px', overflowX: 'auto'}}>{JSON.stringify(act.input, null, 2)}</pre>
                          </div>
                        ))}
                      </div>
                    </details>
                  )}
                  
                  {/* Final Answer */}
                  {msg.content && (
                    <div className="final-answer markdown-body" dangerouslySetInnerHTML={renderMarkdown(msg.content)} />
                  )}
                </div>
              </div>
            );
          } else if (msg.role === 'error') {
            return (
              <div key={idx} className="message" style={{color: 'var(--accent-red)', justifyContent: 'center', maxWidth: '100%'}}>
                ⚠️ {msg.content}
              </div>
            );
          }
          return null;
        })}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <textarea
          id="chat-input"
          placeholder="What should we do today?"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
        />
        <button className="glass-btn primary-btn" onClick={handleSubmit} disabled={isProcessing}>
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        </button>
      </div>
    </div>
  );
}

export default ChatTerminal;
