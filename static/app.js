// Global Logs
const activityLog = [];
const traceLog = [];

function logActivity(message) {
    const time = new Date().toLocaleTimeString();
    activityLog.push({ time, message });
}

function logTrace(message) {
    const time = new Date().toLocaleTimeString();
    traceLog.push({ time, message });
}

document.addEventListener('DOMContentLoaded', () => {
    fetchFiles();

    // Setup Enter key to send
    document.getElementById('chat-input').addEventListener('keypress', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            document.getElementById('send-btn').click();
        }
    });

    document.getElementById('send-btn').addEventListener('click', () => {
        const input = document.getElementById('chat-input');
        const text = input.value.trim();
        if (text) {
            sendChat(text);
            input.value = '';
        }
    });

    document.getElementById('file-upload').addEventListener('change', async (e) => {
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
            alert('上传失败: ' + error);
        }
    });

    // --- 拖拽上传支持 (Drag and Drop) ---
    const leftDrawer = document.querySelector('.left-drawer');

    leftDrawer.addEventListener('dragover', (e) => {
        e.preventDefault();
        leftDrawer.classList.add('drag-over');
    });

    leftDrawer.addEventListener('dragleave', (e) => {
        e.preventDefault();
        leftDrawer.classList.remove('drag-over');
    });

    leftDrawer.addEventListener('drop', async (e) => {
        e.preventDefault();
        leftDrawer.classList.remove('drag-over');
        
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                logActivity(`上传了文件: ${file.name}`);
                alert(data.info);
                fetchFiles();
            } catch (error) {
                logActivity(`文件上传失败: ${error}`);
                alert('上传失败: ' + error);
            }
        }
    });
});

// --- Modal Logic ---
function openModal(type) {
    const modal = document.getElementById('hud-modal');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('modal-body');
    
    modal.classList.remove('hidden');
    body.innerHTML = '';

    if (type === 'activity') {
        title.textContent = '🔔 System Activity Log';
        if (activityLog.length === 0) {
            body.innerHTML = '<div class="log-entry info">暂无活动记录</div>';
        } else {
            activityLog.forEach(log => {
                body.innerHTML += `<div class="log-entry info"><span class="log-time">[${log.time}]</span> ${log.message}</div>`;
            });
        }
    } else if (type === 'trace') {
        title.textContent = '⚙️ Agent Trace Log';
        if (traceLog.length === 0) {
            body.innerHTML = '<div class="log-entry trace">暂无底层执行日志</div>';
        } else {
            traceLog.forEach(log => {
                body.innerHTML += `<div class="log-entry trace"><span class="log-time">[${log.time}]</span> ${log.message}</div>`;
            });
        }
    } else if (type === 'context') {
        title.textContent = '🧠 Context Memory Viewer';
        body.innerHTML = '<div class="log-entry context">Loading memory...</div>';
        fetch('/api/context')
            .then(res => res.json())
            .then(data => {
                body.innerHTML = '';
                data.history.forEach((msg, idx) => {
                    const role = msg.role.toUpperCase();
                    body.innerHTML += `<div class="log-entry context"><strong>[${idx}] ${role}</strong>\n${JSON.stringify(msg, null, 2)}</div>`;
                });
                if (data.history.length === 0) body.innerHTML = '<div class="log-entry context">Memory is empty</div>';
            })
            .catch(err => {
                body.innerHTML = `<div class="log-entry" style="color:red">Failed to load context: ${err}</div>`;
            });
    } else if (type === 'settings') {
        title.textContent = '🔌 Settings Hub';
        const template = document.getElementById('settings-template');
        body.innerHTML = template.innerHTML;
        
        // Fetch current config
        fetch('/api/config')
            .then(res => res.json())
            .then(data => {
                document.getElementById('config-base-url').value = data.base_url;
                document.getElementById('config-api-key').value = data.api_key;
                document.getElementById('config-model-name').value = data.model_name;
            });
    }
}

async function fetchModels() {
    const btn = document.querySelector('.model-select-group .action-btn');
    const oldText = btn.textContent;
    btn.textContent = '拉取中...';
    btn.disabled = true;

    const apiKey = document.getElementById('config-api-key').value;
    const baseUrl = document.getElementById('config-base-url').value;

    try {
        const response = await fetch(`/api/models?api_key=${encodeURIComponent(apiKey)}&base_url=${encodeURIComponent(baseUrl)}`);
        const data = await response.json();
        
        if (response.ok && data.models) {
            const datalist = document.getElementById('model-options');
            datalist.innerHTML = '';
            data.models.forEach(m => {
                const option = document.createElement('option');
                option.value = m;
                datalist.appendChild(option);
            });
            alert(`成功拉取了 ${data.models.length} 个可用模型！请在输入框下拉选择。`);
        } else {
            alert(data.error || "拉取失败，这可能是不支持标准接口。");
        }
    } catch (e) {
        alert("网络错误：" + e);
    } finally {
        btn.textContent = oldText;
        btn.disabled = false;
    }
}

async function saveConfig() {
    const data = {
        api_key: document.getElementById('config-api-key').value,
        base_url: document.getElementById('config-base-url').value,
        model_name: document.getElementById('config-model-name').value
    };

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (result.status === 'success') {
            logActivity("修改了大模型 API 配置");
            alert(result.message);
            closeModal();
        } else {
            alert("保存失败：" + result.message);
        }
    } catch (e) {
        alert("网络错误：" + e);
    }
}

function closeModal() {
    document.getElementById('hud-modal').classList.add('hidden');
}

async function fetchFiles() {
    try {
        const response = await fetch('/api/files');
        const data = await response.json();
        
        const renderList = (files, containerId) => {
            const container = document.getElementById(containerId);
            container.innerHTML = '';
            if (files.length === 0) {
                container.innerHTML = '<div class="file-item" style="color:#666;text-align:center;">Empty</div>';
            } else {
                files.forEach(f => {
                    const el = document.createElement('div');
                    el.className = 'file-item';
                    
                    let icon = '📄';
                    if (f.name.toLowerCase().endsWith('.json')) {
                        icon = '🗂️';
                    } else if (f.name.toLowerCase().endsWith('.txt')) {
                        icon = '📝';
                    }
                    
                    el.innerHTML = `<a href="/${f.path}" target="_blank" style="color: inherit; text-decoration: none; display: block;" title="点击快捷查看/下载">${icon} ${f.name}</a>`;
                    container.appendChild(el);
                });
            }
        };

        renderList(data.input, 'input-file-list');
        renderList(data.output, 'output-file-list');
    } catch (e) {
        console.error("加载文件列表失败", e);
    }
}

function appendUserMessage(text) {
    const messages = document.getElementById('chat-messages');
    const msg = document.createElement('div');
    msg.className = 'message user-message';
    msg.innerHTML = `
        <div class="avatar">U</div>
        <div class="content">${text.replace(/\n/g, '<br>')}</div>
    `;
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
}

function sendChat(query) {
    appendUserMessage(query);

    const messages = document.getElementById('chat-messages');
    
    // Create AI response container
    const aiMsg = document.createElement('div');
    aiMsg.className = 'message ai-message';
    
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = 'AI';
    
    const content = document.createElement('div');
    content.className = 'content';
    
    const stateIndicator = document.createElement('div');
    stateIndicator.className = 'state-indicator';
    stateIndicator.innerHTML = '<span class="dot"></span> <span class="state-text">思考中...</span>';
    content.appendChild(stateIndicator);
    
    aiMsg.appendChild(avatar);
    aiMsg.appendChild(content);
    messages.appendChild(aiMsg);
    messages.scrollTop = messages.scrollHeight;

    // Connect SSE
    const eventSource = new EventSource('/api/chat?query=' + encodeURIComponent(query));
    let hasAnswer = false;

    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        const stateText = stateIndicator.querySelector('.state-text');
        
        if (data.type === 'thought') {
            if(stateText) stateText.textContent = '深入思考中...';
            logTrace(`[Thought] ${data.content}`);
        } 
        else if (data.type === 'action') {
            if(stateText) stateText.textContent = `正在调用工具: ${data.function}...`;
            logTrace(`[Action] Calling ${data.function} with args: ${JSON.stringify(data.args)}`);
            logActivity(`调用底层工具: ${data.function}`);
        }
        else if (data.type === 'observation') {
            if(stateText) stateText.textContent = '获取到结果，分析中...';
            logTrace(`[Observation] ${data.content}`);
            fetchFiles(); // Auto refresh file list after actions
        }
        else if (data.type === 'answer') {
            const textDiv = document.createElement('div');
            textDiv.innerHTML = data.content.replace(/\n/g, '<br>');
            content.appendChild(textDiv);
            
            // 彻底移除状态指示器
            stateIndicator.remove();
            
            logTrace(`[Answer] Generated response.`);
            hasAnswer = true;
            eventSource.close();
            fetchFiles();
        }
        else if (data.type === 'error') {
            stateIndicator.remove();
            content.innerHTML += `<div style="color:red;margin-top:10px;">[Error] ${data.content}</div>`;
            logTrace(`[Error] ${data.content}`);
            eventSource.close();
        }
        
        messages.scrollTop = messages.scrollHeight;
    };

    eventSource.onerror = function(err) {
        console.error("SSE Error:", err);
        if (!hasAnswer) {
            stateIndicator.remove();
            content.innerHTML += `<div style="color:red;margin-top:10px;">[Network Error] 连接断开</div>`;
        }
        eventSource.close();
    };
}
