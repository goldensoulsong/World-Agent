import React, { useState, useEffect } from 'react';

function SystemHudModal({ isOpen, onClose, activeTab: initialTab, sessionId }) {
  const [activeTab, setActiveTab] = useState(initialTab || 'logs');
  const [logsData, setLogsData] = useState([]);
  const [traceData, setTraceData] = useState({ rounds: [] });
  const [contextData, setContextData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedRounds, setExpandedRounds] = useState({});
  const [copiedIdx, setCopiedIdx] = useState(null);

  // Sync tab when prop changes
  useEffect(() => {
    if (initialTab) setActiveTab(initialTab);
  }, [initialTab]);

  // Fetch data when opened or tab changes
  useEffect(() => {
    if (!isOpen || !sessionId) return;
    
    setLoading(true);
    
    if (activeTab === 'logs') {
      fetch(`/api/logs/${sessionId}`)
        .then(r => r.json())
        .then(data => { setLogsData(data.logs || []); setLoading(false); })
        .catch(() => setLoading(false));
    } else if (activeTab === 'trace') {
      fetch(`/api/trace/${sessionId}`)
        .then(r => r.json())
        .then(data => { setTraceData(data); setLoading(false); })
        .catch(() => setLoading(false));
    } else if (activeTab === 'context') {
      fetch(`/api/context?session_id=${sessionId}`)
        .then(r => r.json())
        .then(data => { setContextData(data.history || []); setLoading(false); })
        .catch(() => setLoading(false));
    }
  }, [isOpen, activeTab, sessionId]);

  if (!isOpen) return null;

  const handleCopy = (text, idx) => {
    const copyText = typeof text === 'string' ? text : JSON.stringify(text, null, 2);
    navigator.clipboard.writeText(copyText).then(() => {
      setCopiedIdx(idx);
      setTimeout(() => setCopiedIdx(null), 1500);
    });
  };

  const formatTimestamp = (ts) => {
    try {
      const d = new Date(ts);
      return d.toLocaleString('zh-CN', { hour12: false });
    } catch { return ts; }
  };

  const toggleRound = (rid) => {
    setExpandedRounds(prev => ({ ...prev, [rid]: !prev[rid] }));
  };

  const eventIcon = (type) => {
    const icons = {
      round_start: '🚀',
      thought_complete: '💭',
      tool_call: '🔧',
      tool_result: '📋',
      answer: '💬',
      error: '❌'
    };
    return icons[type] || '📌';
  };

  const eventLabel = (type) => {
    const labels = {
      round_start: '用户输入',
      thought_complete: 'AI 思考',
      tool_call: '工具调用',
      tool_result: '工具返回',
      answer: '最终回答',
      error: '错误'
    };
    return labels[type] || type;
  };

  // ============ Render: Logs Tab ============
  const renderLogs = () => {
    if (logsData.length === 0) {
      return <div className="hud-empty">暂无日志数据，发送一条消息后即可查看</div>;
    }

    // Group by sent/received pairs
    const pairs = [];
    for (let i = 0; i < logsData.length; i++) {
      const entry = logsData[i];
      if (entry.direction === 'sent') {
        const received = logsData[i + 1]?.direction === 'received' ? logsData[i + 1] : null;
        pairs.push({ sent: entry, received });
        if (received) i++;
      } else {
        pairs.push({ sent: null, received: entry });
      }
    }

    return pairs.map((pair, idx) => (
      <div key={idx} className="log-io-pair">
        <div className="log-pair-header">
          <span className="log-pair-num">#{idx + 1}</span>
          <span className="log-pair-time">{pair.sent ? formatTimestamp(pair.sent.timestamp) : formatTimestamp(pair.received?.timestamp)}</span>
        </div>
        
        {pair.sent && (
          <div className="log-io-block sent">
            <div className="log-io-label">
              <span className="log-io-icon">📤</span> SENT — 完整 Messages 数组
              <button 
                className="hud-copy-btn" 
                onClick={() => handleCopy(pair.sent.raw_content, `s${idx}`)}
              >
                {copiedIdx === `s${idx}` ? '✓ 已复制' : '复制'}
              </button>
            </div>
            <pre className="log-io-content">{typeof pair.sent.raw_content === 'string' 
              ? pair.sent.raw_content 
              : JSON.stringify(pair.sent.raw_content, null, 2)}
            </pre>
          </div>
        )}
        
        {pair.received && (
          <div className="log-io-block received">
            <div className="log-io-label">
              <span className="log-io-icon">📥</span> RECEIVED — AI 原始输出
              <button 
                className="hud-copy-btn" 
                onClick={() => handleCopy(pair.received.raw_content, `r${idx}`)}
              >
                {copiedIdx === `r${idx}` ? '✓ 已复制' : '复制'}
              </button>
            </div>
            <pre className="log-io-content">{typeof pair.received.raw_content === 'string' 
              ? pair.received.raw_content 
              : JSON.stringify(pair.received.raw_content, null, 2)}
            </pre>
          </div>
        )}
      </div>
    ));
  };

  // ============ Render: Trace Tab ============
  const renderTrace = () => {
    const rounds = traceData.rounds || [];
    if (rounds.length === 0) {
      return <div className="hud-empty">暂无追踪数据，发送一条消息后即可查看</div>;
    }

    return rounds.map((round, rIdx) => {
      const isExpanded = expandedRounds[round.round_id] !== false; // default open
      const events = round.events || [];
      const startEvent = events.find(e => e.event_type === 'round_start');
      const userQuery = startEvent?.content || '(未知)';
      const toolCount = events.filter(e => e.event_type === 'tool_call').length;
      const hasError = events.some(e => e.event_type === 'error');

      return (
        <div key={round.round_id} className={`trace-round ${hasError ? 'has-error' : ''}`}>
          <div className="trace-round-header" onClick={() => toggleRound(round.round_id)}>
            <div className="trace-round-info">
              <span className="trace-round-num">Round #{rIdx + 1}</span>
              <span className="trace-round-query">{userQuery.length > 60 ? userQuery.substring(0, 60) + '...' : userQuery}</span>
            </div>
            <div className="trace-round-meta">
              {toolCount > 0 && <span className="trace-round-badge">🔧 ×{toolCount}</span>}
              <span className="trace-round-time">{formatTimestamp(round.started_at)}</span>
              <span className={`trace-round-arrow ${isExpanded ? 'expanded' : ''}`}>▾</span>
            </div>
          </div>
          
          {isExpanded && (
            <div className="trace-timeline">
              {events.map((evt, eIdx) => (
                <div key={eIdx} className={`trace-event trace-event-${evt.event_type}`}>
                  <div className="trace-event-dot">
                    <span className="trace-event-icon">{eventIcon(evt.event_type)}</span>
                    {eIdx < events.length - 1 && <div className="trace-event-line"></div>}
                  </div>
                  <div className="trace-event-body">
                    <div className="trace-event-header">
                      <span className="trace-event-label">{eventLabel(evt.event_type)}</span>
                      <span className="trace-event-time">{formatTimestamp(evt.timestamp)}</span>
                    </div>
                    <div className="trace-event-content">
                      {evt.event_type === 'tool_call' ? (
                        <>
                          <div className="trace-tool-name">{evt.content}</div>
                          {evt.metadata?.args && (
                            <pre className="trace-code-block">{JSON.stringify(evt.metadata.args, null, 2)}</pre>
                          )}
                        </>
                      ) : evt.event_type === 'tool_result' ? (
                        <>
                          {evt.metadata?.tool_name && <div className="trace-tool-name">← {evt.metadata.tool_name}</div>}
                          <pre className="trace-code-block">{
                            typeof evt.content === 'string' 
                              ? (evt.content.length > 2000 ? evt.content.substring(0, 2000) + '\n...[折叠]' : evt.content)
                              : JSON.stringify(evt.content, null, 2)
                          }</pre>
                        </>
                      ) : (
                        <pre className="trace-text-block">{
                          typeof evt.content === 'string' 
                            ? (evt.content.length > 3000 ? evt.content.substring(0, 3000) + '\n...[折叠]' : evt.content) 
                            : JSON.stringify(evt.content, null, 2)
                        }</pre>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    });
  };

  // ============ Render: Context Tab ============
  const renderContext = () => {
    if (contextData.length === 0) {
      return <div className="hud-empty">暂无上下文数据</div>;
    }

    return contextData.map((msg, idx) => {
      const roleConfig = {
        system: { icon: '⚙️', label: 'System Prompt', className: 'ctx-system' },
        user: { icon: '👤', label: '用户', className: 'ctx-user' },
        assistant: { icon: '🤖', label: 'AI 助手', className: 'ctx-assistant' }
      };
      const config = roleConfig[msg.role] || { icon: '📌', label: msg.role, className: 'ctx-other' };

      return (
        <div key={idx} className={`ctx-message ${config.className}`}>
          <div className="ctx-message-header">
            <span className="ctx-role-icon">{config.icon}</span>
            <span className="ctx-role-label">{config.label}</span>
            <span className="ctx-msg-num">#{idx + 1}</span>
            <button 
              className="hud-copy-btn" 
              onClick={() => handleCopy(msg.content, `ctx${idx}`)}
            >
              {copiedIdx === `ctx${idx}` ? '✓ 已复制' : '复制'}
            </button>
          </div>
          <pre className="ctx-message-content">{msg.content}</pre>
        </div>
      );
    });
  };

  const tabs = [
    { key: 'logs', icon: '🔔', label: '日志' },
    { key: 'trace', icon: '⚙️', label: '追踪' },
    { key: 'context', icon: '🧠', label: '记忆' }
  ];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content hud-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>SYSTEM HUD</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        {/* Tab Bar */}
        <div className="hud-tab-bar">
          {tabs.map(tab => (
            <button
              key={tab.key}
              className={`hud-tab ${activeTab === tab.key ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.key)}
            >
              <span className="hud-tab-icon">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
          <div className="hud-session-badge">Session: {sessionId ? sessionId.substring(0, 12) : '—'}</div>
        </div>

        {/* Tab Content */}
        <div className="modal-body hud-body">
          {loading ? (
            <div className="hud-loading">
              <div className="hud-loading-dot"></div>
              <span>加载中...</span>
            </div>
          ) : (
            <>
              {activeTab === 'logs' && renderLogs()}
              {activeTab === 'trace' && renderTrace()}
              {activeTab === 'context' && renderContext()}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default SystemHudModal;
