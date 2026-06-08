import React, { useState, useEffect } from 'react';

function FileWorkspace() {
  const [inputFiles, setInputFiles] = useState([]);
  const [outputFiles, setOutputFiles] = useState([]);

  const fetchFiles = async () => {
    try {
      const response = await fetch('/api/files');
      const data = await response.json();
      setInputFiles(data.input || []);
      setOutputFiles(data.output || []);
    } catch (e) {
      console.error('Failed to load files', e);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      alert(data.info);
      fetchFiles();
    } catch (error) {
      alert('Upload failed: ' + error);
    }
  };

  const deleteFile = async (filePath) => {
    if (!window.confirm(`确定要彻底删除文件 ${filePath} 吗？\n此操作不可恢复。`)) return;
    try {
      const response = await fetch(`/api/files?path=${encodeURIComponent(filePath)}`, {
        method: 'DELETE'
      });
      const result = await response.json();
      if (response.ok) {
        fetchFiles();
      } else {
        alert(result.error || "删除失败");
      }
    } catch (e) {
      alert("网络错误: " + e);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('drag-over');
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');
    const filePath = e.dataTransfer.getData('text/plain');
    if (filePath) {
      deleteFile(filePath);
    }
  };

  const renderFileList = (files) => {
    if (files.length === 0) {
      return <div className="file-item" style={{ color: '#666', textAlign: 'center' }}>Empty</div>;
    }
    return files.map(f => {
      let icon = '📄';
      if (f.name.toLowerCase().endsWith('.json')) icon = '🗂️';
      else if (f.name.toLowerCase().endsWith('.txt')) icon = '📝';
      
      return (
        <div 
          key={f.path} 
          className="file-item" 
          draggable 
          onDragStart={(e) => {
            e.dataTransfer.setData('text/plain', f.path);
            e.dataTransfer.effectAllowed = 'move';
          }}
        >
          <a href={`/${f.path}`} className="file-name-link" target="_blank" rel="noreferrer" title="点击查看/下载">
            {icon} {f.name}
          </a>
        </div>
      );
    });
  };

  return (
    <aside className="right-sidebar">
      {/* Input Zone */}
      <div className="right-panel-section glass-panel">
        <div className="panel-header">
          <h2>📥 Input Zone</h2>
          <p>workspace/input</p>
        </div>
        <div className="upload-section">
          <input type="file" id="file-upload" className="file-input" onChange={handleFileUpload} />
          <label htmlFor="file-upload" className="upload-btn dynamic-btn">
            <span className="upload-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
            </span>
            <span className="upload-text">导入文件 (Import)</span>
            <div className="btn-glow"></div>
          </label>
        </div>
        <div className="file-list" id="input-file-list">
          {renderFileList(inputFiles)}
        </div>
        <div className="quick-actions">
          <button className="action-btn glass-btn">🔪 智能切块 (Smart Chunk)</button>
        </div>
      </div>

      {/* Output Zone */}
      <div className="right-panel-section glass-panel">
        <div className="panel-header">
          <h2>📦 Output Zone</h2>
          <p>workspace/output</p>
        </div>
        <div className="file-list" id="output-file-list">
          {renderFileList(outputFiles)}
        </div>
        <div className="quick-actions">
          <button className="action-btn glass-btn">📄 合并导出 TXT</button>
        </div>
      </div>

      {/* Trash Zone */}
      <div 
        className="trash-zone" 
        id="trash-zone"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="trash-icon">🗑️</div>
        <div className="trash-text">将文件拖拽至此删除</div>
      </div>
    </aside>
  );
}

export default FileWorkspace;
