import React, { useState } from 'react';

function Sidebar({ sessions, currentSessionId, onNewChat, onSelectSession, onDeleteSession, onOpenSettings, onOpenHud }) {
  const [agentOpen, setAgentOpen] = useState(false);
  const [activeAgent, setActiveAgent] = useState('text_processing');
  
  const openModal = (type) => {
    if (type === 'settings') {
      if (onOpenSettings) onOpenSettings();
    } else if (type === 'activity' && onOpenHud) {
      onOpenHud('logs');
    } else if (type === 'trace' && onOpenHud) {
      onOpenHud('trace');
    } else if (type === 'context' && onOpenHud) {
      onOpenHud('context');
    }
  };

  return (
    <aside className="left-sidebar glass-panel" style={{display: 'flex', flexDirection: 'column'}}>
      <div className="brand">
        <h1>World-Agent</h1>
        <p>Nexus System</p>
      </div>

      <div className="sidebar-section">
        <h3>MODULES</h3>
        <div className="custom-select-wrapper">
          <div className={`custom-select ${agentOpen ? 'open' : ''}`} onClick={() => setAgentOpen(!agentOpen)}>
            <div className="select-trigger">
              <span className="selected-text">
                {activeAgent === 'text_processing' ? '✍️ 文本处理 Agent' : '🧠 知识库 Agent (待接入)'}
              </span>
              <div className="select-arrow">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
              </div>
            </div>
            <div className="select-options">
              <div className={`option ${activeAgent === 'text_processing' ? 'selected' : ''}`} onClick={() => setActiveAgent('text_processing')}>✍️ 文本处理 Agent</div>
              <div className={`option ${activeAgent === 'rag_knowledge' ? 'selected' : ''}`} onClick={(e) => { e.stopPropagation(); alert('RAG 知识库 Agent 正在建设中，敬请期待！'); }}>🧠 知识库 Agent (待接入)</div>
            </div>
          </div>
        </div>
      </div>

      <div className="sidebar-section history-section">
        <div className="history-header">
          <h3>💬 ARCHIVES</h3>
          <button className="new-chat-btn" onClick={onNewChat} title="新建对话">
            + New
          </button>
        </div>
        
        <div className="chat-history-list">
          {/* Optimistic new session if currently in one that isn't saved yet */}
          {currentSessionId && !sessions.find(s => s.id === currentSessionId) && (
            <div className="chat-history-item active" title="新对话 (未保存)">
              <span className="chat-title-text">新对话...</span>
            </div>
          )}

          {sessions.length === 0 && !currentSessionId ? (
             <div className="history-empty">无历史会话</div>
          ) : (
            sessions.map(sess => (
              <div 
                key={sess.id}
                onClick={() => onSelectSession(sess.id)}
                className={`chat-history-item ${currentSessionId === sess.id ? 'active' : ''}`}
                title={sess.title}
              >
                <span className="chat-title-text">{sess.title}</span>
                <button 
                  className="chat-delete-btn" 
                  title="删除记录" 
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(sess.id);
                  }}
                >
                  ✕
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="sidebar-section bottom-section" style={{marginTop: 'auto'}}>
        <h3>SYSTEM HUD</h3>
        <div className="hud-controls-vertical">
          <button className="hud-btn" onClick={() => openModal('settings')} title="Settings Hub">🔌 配置</button>
          <button className="hud-btn" onClick={() => openModal('activity')} title="System Activity Log">🔔 日志</button>
          <button className="hud-btn" onClick={() => openModal('trace')} title="Agent Trace Log">⚙️ 追踪</button>
          <button className="hud-btn" onClick={() => openModal('context')} title="Context Memory">🧠 记忆</button>
        </div>
        <div className="status-indicator">
          <span className="dot"></span> Online
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
