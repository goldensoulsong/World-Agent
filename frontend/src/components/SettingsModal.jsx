import React, { useState, useEffect } from 'react';

function SettingsModal({ isOpen, onClose }) {
  const [config, setConfig] = useState({
    api_key: '',
    base_url: '',
    model_name: ''
  });
  const [availableModels, setAvailableModels] = useState([]);
  const [isFetchingModels, setIsFetchingModels] = useState(false);
  const [showModelDropdown, setShowModelDropdown] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');

  // Fetch initial config
  useEffect(() => {
    if (isOpen) {
      fetch('/api/config')
        .then(res => res.json())
        .then(data => {
          setConfig({
            api_key: data.api_key || '',
            base_url: data.base_url || '',
            model_name: data.model_name || 'deepseek-chat'
          });
        })
        .catch(err => console.error("Failed to load config", err));
    }
  }, [isOpen]);

  // Handle input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    setConfig(prev => ({ ...prev, [name]: value }));
  };

  // Fetch models
  const handleFetchModels = async () => {
    setIsFetchingModels(true);
    setSaveStatus('');
    try {
      const res = await fetch('/api/models', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: config.api_key,
          base_url: config.base_url
        })
      });
      const data = await res.json();
      if (res.ok && data.models) {
        setAvailableModels(data.models);
        setShowModelDropdown(true);
        if (data.models.length > 0 && !data.models.includes(config.model_name)) {
            setConfig(prev => ({ ...prev, model_name: data.models[0] }));
        }
      } else {
        setSaveStatus(data.error || '拉取模型失败，请检查 API Key 和 Base URL。');
      }
    } catch (e) {
      console.error(e);
      setSaveStatus('网络错误，拉取失败。');
    }
    setIsFetchingModels(false);
  };

  // Select model from dropdown
  const handleSelectModel = (model) => {
    setConfig(prev => ({ ...prev, model_name: model }));
    setShowModelDropdown(false);
  };

  // Save config
  const handleSave = async () => {
    setSaveStatus('保存中...');
    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      const data = await res.json();
      if (res.ok) {
        setSaveStatus('保存成功！Agent 已热重载。');
        setTimeout(() => {
          setSaveStatus('');
          onClose();
        }, 1500);
      } else {
        setSaveStatus(data.error || '保存失败。');
      }
    } catch (e) {
      setSaveStatus('网络错误，保存失败。');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content glass-panel" style={{ width: '500px', height: 'auto', minHeight: '400px' }}>
        <div className="modal-header">
          <h2>系统配置 (Nexus Settings)</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>
        <div className="modal-body">
          <div className="settings-form">
            <div className="form-group">
              <label>API Key</label>
              <input
                type="password"
                name="api_key"
                className="glass-input"
                value={config.api_key}
                onChange={handleChange}
                placeholder="sk-..."
              />
            </div>
            <div className="form-group">
              <label>Base URL (选填)</label>
              <input
                type="text"
                name="base_url"
                className="glass-input"
                value={config.base_url}
                onChange={handleChange}
                placeholder="https://api.deepseek.com"
              />
            </div>
            <div className="form-group">
              <label>模型名称 (Model)</label>
              <div className="model-select-group" style={{ position: 'relative' }}>
                <input
                  type="text"
                  name="model_name"
                  className="glass-input"
                  value={config.model_name}
                  onChange={handleChange}
                  placeholder="deepseek-chat"
                />
                <button 
                  className="glass-btn" 
                  onClick={handleFetchModels}
                  disabled={isFetchingModels}
                >
                  {isFetchingModels ? '获取中...' : '拉取列表'}
                </button>
                
                {showModelDropdown && availableModels.length > 0 && (
                  <div className="glass-panel" style={{ 
                    position: 'absolute', 
                    top: '100%', 
                    left: 0, 
                    right: 0, 
                    marginTop: '8px', 
                    zIndex: 10,
                    maxHeight: '200px',
                    overflowY: 'auto',
                    padding: '0'
                  }}>
                    {availableModels.map(model => (
                      <div 
                        key={model} 
                        className="model-item"
                        onClick={() => handleSelectModel(model)}
                      >
                        {model}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {saveStatus && (
              <div style={{ marginTop: '10px', fontSize: '0.9rem', color: saveStatus.includes('成功') ? 'var(--accent-blue)' : 'var(--accent-red)' }}>
                {saveStatus}
              </div>
            )}

            <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button className="glass-btn" onClick={onClose}>取消</button>
              <button className="glass-btn primary-btn" onClick={handleSave}>保存配置</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsModal;
