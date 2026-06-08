import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatTerminal from './components/ChatTerminal';
import FileWorkspace from './components/FileWorkspace';
import Mascot from './components/Mascot';
import SettingsModal from './components/SettingsModal';
import SystemHudModal from './components/SystemHudModal';

function App() {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState('');
  const [agentState, setAgentState] = useState('idle'); // idle, thinking, working
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isHudOpen, setIsHudOpen] = useState(false);
  const [hudActiveTab, setHudActiveTab] = useState('logs');

  // Generate a new session ID
  const generateSessionId = () => 'sess_' + Math.random().toString(36).substr(2, 9);

  // Fetch all sessions from backend
  const fetchSessions = async () => {
    try {
      const response = await fetch('/api/chats');
      const data = await response.json();
      setSessions(data.chats || []);
      
      // If we have sessions but no current session, pick the first one
      if (data.chats.length > 0 && !currentSessionId) {
        setCurrentSessionId(data.chats[0].id);
      } else if (data.chats.length === 0 && !currentSessionId) {
        // If completely empty, start a new one
        setCurrentSessionId(generateSessionId());
      }
    } catch (e) {
      console.error("Failed to fetch sessions", e);
      if (!currentSessionId) setCurrentSessionId(generateSessionId());
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []); // Run once on mount

  const handleNewChat = () => {
    setCurrentSessionId(generateSessionId());
  };

  const handleSelectSession = (id) => {
    setCurrentSessionId(id);
  };

  const handleDeleteSession = async (id) => {
    if (!window.confirm('确定要删除这个对话记录吗？')) return;
    try {
      const res = await fetch(`/api/chats/${id}`, { method: 'DELETE' });
      if (res.ok) {
        setSessions(prev => prev.filter(s => s.id !== id));
        if (currentSessionId === id) {
          setCurrentSessionId(generateSessionId());
        }
      }
    } catch (e) {
      console.error("Failed to delete session", e);
    }
  };

  const handleOpenHud = (tab) => {
    setHudActiveTab(tab);
    setIsHudOpen(true);
  };

  return (
    <div className="app-container">
      <Sidebar 
        sessions={sessions} 
        currentSessionId={currentSessionId} 
        onNewChat={handleNewChat}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenHud={handleOpenHud}
      />
      {/* We use key={currentSessionId} to force remount the chat terminal when switching sessions */}
      {currentSessionId && (
        <ChatTerminal 
          key={currentSessionId}
          sessionId={currentSessionId} 
          setAgentState={setAgentState} 
          refreshSessions={fetchSessions}
        />
      )}
      <FileWorkspace />
      <Mascot agentState={agentState} />
      <SettingsModal 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
      />
      <SystemHudModal
        isOpen={isHudOpen}
        onClose={() => setIsHudOpen(false)}
        activeTab={hudActiveTab}
        sessionId={currentSessionId}
      />
      <div style={{display: 'none'}} data-version="v4-cache-bust"></div>
    </div>
  );
}

export default App;
