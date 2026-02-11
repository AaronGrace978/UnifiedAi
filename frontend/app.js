// Brain Thinker - Deep Reasoning Interface
// Neural network visual integration

const API_BASE = 'http://localhost:10000/api';

let chatHistory = [];
let conversationId = null; // Persistent across messages for memory continuity

// Idle/Lock Screen Functions
function showIdleScreen() {
    // Add transition effect
    document.body.style.transition = 'opacity 0.5s ease-in';
    document.body.style.opacity = '0';

    // Navigate to idle screen after transition
    setTimeout(() => {
        window.location.href = 'idle.html';
    }, 500);
}

function returnFromIdle() {
    // This function can be called from the idle screen to return
    window.location.href = 'index.html';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    // Ensure chat tab (Brain Thinker) is active on load
    switchTab('chat');
    checkBrainStatus();
    loadModels();
    loadMemoryStats();
    loadPatterns();
    initializeAnimations();
});

function initializeAnimations() {
    // Add ripple effect to all buttons
    document.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', createRipple);
    });
    
    // Staggered reveal for initial elements
    const chatMessages = document.querySelector('.chat-messages');
    if (chatMessages) {
        chatMessages.querySelectorAll('.message').forEach((msg, i) => {
            msg.style.animationDelay = `${i * 0.1}s`;
        });
    }
}

function createRipple(e) {
    const button = e.currentTarget;
    const rect = button.getBoundingClientRect();
    const ripple = document.createElement('span');
    
    ripple.style.cssText = `
        position: absolute;
        width: 100px;
        height: 100px;
        background: rgba(255,255,255,0.3);
        border-radius: 50%;
        transform: translate(-50%, -50%) scale(0);
        animation: ripple-expand 0.6s ease-out forwards;
        pointer-events: none;
        left: ${e.clientX - rect.left}px;
        top: ${e.clientY - rect.top}px;
    `;
    
    button.style.position = 'relative';
    button.style.overflow = 'hidden';
    button.appendChild(ripple);
    
    setTimeout(() => ripple.remove(), 600);
}

// Add ripple animation
const rippleStyle = document.createElement('style');
rippleStyle.textContent = `
    @keyframes ripple-expand {
        to { transform: translate(-50%, -50%) scale(4); opacity: 0; }
    }
`;
document.head.appendChild(rippleStyle);

function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Chat
    document.getElementById('sendBtn').addEventListener('click', sendChatMessage);
    document.getElementById('chatInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
    
    // Deep Think
    document.getElementById('thinkBtn').addEventListener('click', submitDeepThink);
    
    // Daemon
    document.getElementById('startDaemon').addEventListener('click', startDaemon);
    document.getElementById('stopDaemon').addEventListener('click', stopDaemon);
    document.getElementById('refreshInsights').addEventListener('click', refreshInsights);
    document.getElementById('exportInsightsJson').addEventListener('click', () => exportInsights('json'));
    document.getElementById('exportInsightsTxt').addEventListener('click', () => exportInsights('txt'));
    
    // Settings
    document.getElementById('refreshModels').addEventListener('click', loadModels);
    document.getElementById('refreshMemoryStats').addEventListener('click', loadMemoryStats);
    document.getElementById('refreshPatterns').addEventListener('click', loadPatterns);
    document.getElementById('settingsModel').addEventListener('change', switchModel);
}

function switchTab(tabName) {
    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.getElementById(`${tabName}Tab`).classList.add('active');
    
    // Load data for specific tabs
    if (tabName === 'daemon') {
        refreshInsights();
    } else if (tabName === 'insights') {
        if (window.InsightsDashboard) {
            window.InsightsDashboard.init();
        }
    } else if (tabName === 'settings') {
        loadMemoryStats();
        loadPatterns();
    }
}

async function checkBrainStatus() {
    try {
        const response = await fetch(`${API_BASE}/brain/status`);
        if (response.ok) {
            const status = await response.json();
            updateStatus(`Connected to ${status.model}`, 'success');
            
            // Update daemon status
            const daemonStatus = document.getElementById('daemonStatus');
            if (status.daemon_running) {
                daemonStatus.querySelector('.status-text').textContent = 'Active';
                daemonStatus.classList.add('active');
            }
        }
    } catch (error) {
        updateStatus('Cannot connect to Brain Thinker backend', 'error');
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addChatMessage('user', message);
    chatHistory.push({ role: 'user', content: message });
    input.value = '';
    
    const deepThink = document.getElementById('deepThinkToggle').checked;
    const talkToMe = document.getElementById('talkToMeToggle')?.checked !== false;
    const coordinatorMode = document.getElementById('coordinatorToggle')?.checked !== false;
    const arenaMode = document.getElementById('arenaToggle')?.checked === true;
    
    const thinkingId = showThinkingIndicator();
    updateStatus(deepThink ? '🔮 Thinking deeply...' : (arenaMode ? '⚡ Arena: agents debating...' : (talkToMe ? '💬 UnifiedAi talking to you...' : '💭 Thinking...')), 'thinking');
    
    if (window.NeuralEffects) {
        window.NeuralEffects.startThinking();
    }
    
    try {
        // Arena Mode: use SSE streaming for live debate panel
        if (arenaMode && !deepThink) {
            await runArenaStreaming(message, thinkingId);
            return;
        }

        const response = await fetch(`${API_BASE}/brain/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                history: chatHistory.slice(-10),
                think_deep: deepThink,
                talk_to_me: talkToMe && !deepThink,
                coordinator_mode: coordinatorMode && !deepThink,
                arena_mode: false,
                conversation_id: conversationId
            })
        });
        
        if (!response.ok) throw new Error('Failed to get response');
        
        const data = await response.json();
        
        // Stop neural effects
        if (window.NeuralEffects) {
            window.NeuralEffects.stopThinking();
        }
        
        // Remove thinking indicator
        removeThinkingIndicator(thinkingId);
        
        let responseContent = data.response;
        if (deepThink && data.confidence) {
            responseContent += `\n\n<em style="color: #a78bfa; font-size: 0.9em;">Confidence: ${(data.confidence * 100).toFixed(0)}%</em>`;
        }
        if (data.talk_to_me_used && !deepThink) {
            responseContent += `\n\n<em style="color: #6ee7b7; font-size: 0.85em;">UnifiedAi talked to you (reflection + advisor)</em>`;
        }
        if (Array.isArray(data.autonomy_actions) && data.autonomy_actions.includes('coordinator') && !deepThink) {
            responseContent += `\n\n<em style="color: #fbbf24; font-size: 0.85em;">Director mode guided internal agents toward your answer</em>`;
        }
        // Arena debate visualization
        if (Array.isArray(data.arena_debate) && data.arena_debate.length > 0) {
            responseContent += renderArenaDebate(data.arena_debate, data.thinking_process);
        }
        if (data.memory_depth > 0) {
            const pct = Math.round(data.memory_depth * 100);
            responseContent += `\n\n<em style="color: #22d3ee; font-size: 0.85em;">Memory depth: ${pct}%</em>`;
        }
        // Persist conversation_id for session continuity
        if (data.conversation_id) {
            conversationId = data.conversation_id;
        }
        
        addChatMessage('assistant', responseContent);
        chatHistory.push({ role: 'assistant', content: data.response });
        
        updateStatus('🧠 Ready', 'success');
        
    } catch (error) {
        if (window.NeuralEffects) {
            window.NeuralEffects.stopThinking();
        }
        removeThinkingIndicator(thinkingId);
        addChatMessage('assistant', 'Sorry, I encountered an error while thinking. Make sure Ollama is running.');
        updateStatus('Error: ' + error.message, 'error');
    }
}

function addChatMessage(role, content) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = role === 'assistant' ? '🧠' : '👤';
    const whoLabel = role === 'assistant' ? '<span class="message-who">UnifiedAi</span> ' : '';
    
    messageDiv.innerHTML = `
        <div class="message-avatar" title="${role === 'assistant' ? 'UnifiedAi' : 'You'}">
            <span>${avatar}</span>
            ${role === 'assistant' ? '<div class="avatar-ring"></div>' : ''}
        </div>
        <div class="message-content">${whoLabel}${formatMessage(content)}</div>
    `;
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function formatMessage(content) {
    // Convert newlines to paragraphs, preserve HTML
    return content.split('\n\n').map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');
}

function showThinkingIndicator() {
    const messagesDiv = document.getElementById('chatMessages');
    const id = 'thinking-' + Date.now();
    
    const thinkingDiv = document.createElement('div');
    thinkingDiv.id = id;
    thinkingDiv.className = 'message assistant';
    thinkingDiv.innerHTML = `
        <div class="message-avatar">
            <span>🧠</span>
            <div class="avatar-ring"></div>
        </div>
        <div class="thinking-indicator">
            <div class="thinking-dots">
                <span></span><span></span><span></span>
            </div>
            <span>Thinking...</span>
        </div>
    `;
    
    messagesDiv.appendChild(thinkingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    return id;
}

function removeThinkingIndicator(id) {
    const indicator = document.getElementById(id);
    if (indicator) indicator.remove();
}

async function loadModels() {
    try {
        const response = await fetch(`${API_BASE}/brain/models`);
        if (!response.ok) throw new Error('Failed to load models');
        
        const data = await response.json();
        const models = data.models;
        const currentModel = data.current_model;
        
        // Populate model selectors
        const thinkModel = document.getElementById('thinkModel');
        const settingsModel = document.getElementById('settingsModel');
        
        thinkModel.innerHTML = '';
        settingsModel.innerHTML = '';
        
        models.forEach(model => {
            const option1 = document.createElement('option');
            option1.value = model;
            option1.textContent = model;
            if (model === currentModel) {
                option1.selected = true;
            }
            thinkModel.appendChild(option1);
            
            const option2 = document.createElement('option');
            option2.value = model;
            option2.textContent = model;
            if (model === currentModel) {
                option2.selected = true;
            }
            settingsModel.appendChild(option2);
        });
        
    } catch (error) {
        console.error('Error loading models:', error);
    }
}

async function submitDeepThink() {
    const input = document.getElementById('problemInput');
    const problem = input.value.trim();
    
    if (!problem) {
        updateStatus('⚠️ Please enter a problem to think about', 'error');
        return;
    }
    
    const mode = document.getElementById('thinkMode').value;
    const model = document.getElementById('thinkModel').value;
    const useMemory = document.getElementById('useMemoryToggle').checked;
    
    // Show thinking process
    const processDiv = document.getElementById('thinkingProcess');
    const thoughtsContainer = document.getElementById('thoughtsContainer');
    const finalAnswerDiv = document.getElementById('finalAnswer');
    
    processDiv.classList.remove('hidden');
    finalAnswerDiv.classList.add('hidden');
    thoughtsContainer.innerHTML = '<div class="thought-item"><div class="thought-type">Starting</div><div class="thought-content">Beginning deep analysis...</div></div>';
    
    updateStatus(`🔮 Thinking in ${mode} mode...`, 'thinking');
    
    // Start neural effects
    if (window.NeuralEffects) {
        window.NeuralEffects.startThinking();
    }
    
    try {
        const response = await fetch(`${API_BASE}/brain/think`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: problem,
                mode: mode,
                model: model || null,
                use_memory: useMemory
            })
        });
        
        if (!response.ok) throw new Error('Thinking failed');
        
        const data = await response.json();
        
        // Stop neural effects
        if (window.NeuralEffects) {
            window.NeuralEffects.stopThinking();
        }
        
        // Display thoughts with animation
        thoughtsContainer.innerHTML = '';
        data.thoughts.forEach((thought, index) => {
            setTimeout(() => {
                const thoughtDiv = document.createElement('div');
                thoughtDiv.className = 'thought-item';
                thoughtDiv.innerHTML = `
                    <div class="thought-type">${thought.type} (${(thought.confidence * 100).toFixed(0)}% confident)</div>
                    <div class="thought-content">${formatThought(thought.content)}</div>
                `;
                thoughtsContainer.appendChild(thoughtDiv);
                thoughtsContainer.scrollTop = thoughtsContainer.scrollHeight;
            }, index * 100);
        });
        
        // Display final answer with delay
        setTimeout(() => {
            document.getElementById('answerContent').textContent = data.answer;
            document.getElementById('answerConfidence').textContent = `${(data.confidence * 100).toFixed(0)}%`;
            document.getElementById('answerIterations').textContent = data.iterations;
            document.getElementById('answerTime').textContent = `${data.thinking_time.toFixed(1)}s`;
            
            finalAnswerDiv.classList.remove('hidden');
            updateStatus('✨ Thinking complete!', 'success');
        }, data.thoughts.length * 100 + 200);
        
    } catch (error) {
        if (window.NeuralEffects) {
            window.NeuralEffects.stopThinking();
        }
        thoughtsContainer.innerHTML = `<div class="thought-item"><div class="thought-type">Error</div><div class="thought-content">${error.message}. Make sure Ollama is running.</div></div>`;
        updateStatus('❌ Error: ' + error.message, 'error');
    }
}

function formatThought(content) {
    // Truncate long thoughts but keep key info
    if (content.length > 500) {
        return content.substring(0, 500) + '...';
    }
    return content.replace(/\n/g, '<br>');
}

async function startDaemon() {
    updateStatus('🚀 Starting background thinking...', 'thinking');
    
    try {
        const response = await fetch(`${API_BASE}/brain/daemon/start`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Failed to start daemon');
        
        const daemonStatus = document.getElementById('daemonStatus');
        daemonStatus.querySelector('.status-text').textContent = 'Active';
        daemonStatus.classList.add('active');
        
        updateStatus('👁️ Background thinking started', 'success');
        
    } catch (error) {
        updateStatus('❌ Error starting daemon: ' + error.message, 'error');
    }
}

async function stopDaemon() {
    try {
        const response = await fetch(`${API_BASE}/brain/daemon/stop`, {
            method: 'POST'
        });
        
        const daemonStatus = document.getElementById('daemonStatus');
        daemonStatus.querySelector('.status-text').textContent = 'Inactive';
        daemonStatus.classList.remove('active');
        
        updateStatus('⏹️ Background thinking stopped', 'success');
        
    } catch (error) {
        updateStatus('❌ Error stopping daemon: ' + error.message, 'error');
    }
}

async function refreshInsights() {
    try {
        const response = await fetch(`${API_BASE}/brain/daemon/insights?limit=10`);
        if (!response.ok) throw new Error('Failed to fetch insights');
        
        const data = await response.json();
        const insightsList = document.getElementById('insightsList');
        
        // Update daemon status
        const daemonStatus = document.getElementById('daemonStatus');
        if (data.is_running) {
            daemonStatus.querySelector('.status-text').textContent = 'Active';
            daemonStatus.classList.add('active');
        } else {
            daemonStatus.querySelector('.status-text').textContent = 'Inactive';
            daemonStatus.classList.remove('active');
        }
        
        if (data.insights.length === 0) {
            insightsList.innerHTML = '<p class="no-insights">No insights yet. Start the background mind to begin generating.</p>';
            return;
        }
        
        insightsList.innerHTML = '';
        data.insights.reverse().forEach((insight, index) => {
            setTimeout(() => {
                const insightDiv = document.createElement('div');
                insightDiv.className = 'insight-item';
                insightDiv.innerHTML = `
                    <div class="insight-time">${new Date(insight.timestamp).toLocaleString()}</div>
                    <div class="insight-content">${insight.content}</div>
                `;
                insightsList.appendChild(insightDiv);
            }, index * 50);
        });
        
    } catch (error) {
        console.error('Error refreshing insights:', error);
    }
}

async function exportInsights(format = 'json') {
    try {
        updateStatus('📥 Exporting insights...', 'info');
        
        const url = format === 'json' 
            ? `${API_BASE}/brain/export/insights/json`
            : `${API_BASE}/brain/export/insights/txt`;
        
        const response = await fetch(url);
        
        if (!response.ok) {
            let errorMsg = 'Failed to export insights';
            try {
                const errorData = await response.json();
                errorMsg = errorData.detail || errorMsg;
            } catch (e) {
                errorMsg = `HTTP ${response.status}: ${response.statusText}`;
            }
            throw new Error(errorMsg);
        }
        
        const blob = await response.blob();
        
        if (blob.size === 0) {
            throw new Error('Received empty file from server');
        }
        
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `unifiedai_insights.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);
        
        updateStatus('✅ Insights exported successfully!', 'success');
    } catch (error) {
        updateStatus('❌ Export failed: ' + error.message, 'error');
        console.error('Error exporting insights:', error);
    }
}

async function loadMemoryStats() {
    try {
        const response = await fetch(`${API_BASE}/brain/memory/stats`);
        if (!response.ok) throw new Error('Failed to load memory stats');
        
        const stats = await response.json();
        const statsDiv = document.getElementById('memoryStats');
        
        statsDiv.innerHTML = `
            <div class="stat-item">
                <strong>Total Sessions:</strong> ${stats.total_sessions}
            </div>
            <div class="stat-item">
                <strong>Average Confidence:</strong> ${(stats.avg_confidence * 100).toFixed(1)}%
            </div>
            <div class="stat-item">
                <strong>Average Thinking Time:</strong> ${stats.avg_thinking_time.toFixed(1)}s
            </div>
            <div class="stat-item">
                <strong>Learned Patterns:</strong> ${stats.total_patterns}
            </div>
        `;
    } catch (error) {
        console.error('Error loading memory stats:', error);
        document.getElementById('memoryStats').innerHTML = '<p>Error loading stats</p>';
    }
}

async function loadPatterns() {
    try {
        const response = await fetch(`${API_BASE}/brain/memory/patterns`);
        if (!response.ok) throw new Error('Failed to load patterns');
        
        const data = await response.json();
        const patterns = data.patterns;
        const patternsDiv = document.getElementById('learnedPatterns');
        
        if (patterns.length === 0) {
            patternsDiv.innerHTML = '<p class="no-data">No patterns learned yet. Start thinking to build patterns!</p>';
            return;
        }
        
        patternsDiv.innerHTML = patterns.slice(0, 10).map(p => `
            <div class="pattern-item">
                <strong>${p.type}:</strong> ${p.data} <span class="pattern-freq">(${p.frequency}x)</span>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading patterns:', error);
        document.getElementById('learnedPatterns').innerHTML = '<p>Error loading patterns</p>';
    }
}

async function switchModel() {
    const model = document.getElementById('settingsModel').value;
    if (!model) return;
    
    updateStatus('🔄 Switching model...', 'thinking');
    
    try {
        const response = await fetch(`${API_BASE}/brain/models/${model}`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Failed to switch model');
        
        updateStatus(`✅ Switched to ${model}`, 'success');
        loadModels(); // Refresh model list
    } catch (error) {
        updateStatus('❌ Error switching model: ' + error.message, 'error');
    }
}

function updateStatus(message, type = '') {
    const statusBar = document.getElementById('statusBar');
    const statusText = document.getElementById('statusText');
    
    statusText.textContent = message;
    statusBar.className = `status-bar ${type}`;
}

// ============================================================
//  ARENA DEBATE VISUALIZATION
// ============================================================

const AGENT_CONFIG = {
    analyst:   { emoji: '🔬', color: '#22d3ee', label: 'Analyst',   glow: 'rgba(34,211,238,0.3)' },
    creative:  { emoji: '🎨', color: '#f472b6', label: 'Creative',  glow: 'rgba(244,114,182,0.3)' },
    critic:    { emoji: '⚔️', color: '#f87171', label: 'Critic',    glow: 'rgba(248,113,113,0.3)' },
    empathist: { emoji: '💜', color: '#a78bfa', label: 'Empathist', glow: 'rgba(167,139,250,0.3)' },
    director:  { emoji: '👁️', color: '#fbbf24', label: 'Director',  glow: 'rgba(251,191,36,0.3)' },
};

function renderArenaDebate(debate, thinkingProcess) {
    // Extract insights from thinking_process
    let insights = [];
    let goals = [];
    if (Array.isArray(thinkingProcess)) {
        for (const t of thinkingProcess) {
            if (t.type === 'arena_insights') insights = t.content.split(' | ');
            if (t.type === 'arena_plan') {
                try { goals = JSON.parse(t.content.replace('goals=', '').replace(/'/g, '"')); } catch(e) {}
            }
        }
    }

    let html = `<div class="arena-debate">`;
    html += `<div class="arena-header">
        <span class="arena-icon">⚡</span>
        <span class="arena-title">Arena Debate</span>
        <button class="arena-toggle-btn" onclick="this.closest('.arena-debate').classList.toggle('collapsed')">▼</button>
    </div>`;

    for (const round of debate) {
        html += `<div class="arena-round">`;
        html += `<div class="arena-round-header">Round ${round.round} — <span class="arena-topic">${escapeHtml(round.topic)}</span></div>`;
        
        for (let i = 0; i < round.messages.length; i++) {
            const msg = round.messages[i];
            const cfg = AGENT_CONFIG[msg.agent_id] || AGENT_CONFIG.analyst;
            const modelShort = msg.model ? msg.model.split(':')[0] : '';
            const delay = (round.round - 1) * 3 + i;
            
            html += `<div class="arena-msg" style="--agent-color: ${cfg.color}; --agent-glow: ${cfg.glow}; animation-delay: ${delay * 0.15}s">
                <div class="arena-msg-avatar" style="background: ${cfg.color}20; border-color: ${cfg.color}">${cfg.emoji}</div>
                <div class="arena-msg-body">
                    <div class="arena-msg-header">
                        <span class="arena-agent-name" style="color: ${cfg.color}">${cfg.label}</span>
                        <span class="arena-model-badge">${escapeHtml(modelShort)}</span>
                    </div>
                    <div class="arena-msg-content">${escapeHtml(msg.content)}</div>
                </div>
            </div>`;
        }
        html += `</div>`;
    }

    // Insights section
    if (insights.length > 0) {
        html += `<div class="arena-insights">
            <div class="arena-insights-header">💡 Key Insights</div>`;
        for (const insight of insights) {
            html += `<div class="arena-insight-item">• ${escapeHtml(insight)}</div>`;
        }
        html += `</div>`;
    }

    html += `</div>`;
    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================
//  ARENA LIVE STREAMING — Side Panel Controller
// ============================================================

function openArenaPanel() {
    const panel = document.getElementById('arenaPanel');
    const overlay = document.getElementById('arenaPanelOverlay');
    const body = document.getElementById('arenaPanelBody');
    const insights = document.getElementById('arenaPanelInsights');
    panel.className = 'arena-panel active';
    overlay.className = 'arena-panel-overlay active';
    body.innerHTML = '';
    insights.innerHTML = '';
    insights.className = 'arena-panel-insights';
    document.getElementById('arenaPanelStatus').textContent = 'Planning debate...';
}

function closeArenaPanel() {
    const panel = document.getElementById('arenaPanel');
    const overlay = document.getElementById('arenaPanelOverlay');
    panel.classList.add('done');
    overlay.classList.remove('active');
    setTimeout(() => {
        panel.className = 'arena-panel';
    }, 700);
}

function updateArenaPanelStatus(text) {
    document.getElementById('arenaPanelStatus').textContent = text;
}

function addArenaPanelErrorCard(message, title = 'Stream Error') {
    const body = document.getElementById('arenaPanelBody');
    const err = document.createElement('div');
    err.className = 'arena-live-round';
    err.innerHTML = `<div class="arena-live-round-header" style="color:#f87171;border-left-color:#f87171;background:rgba(248,113,113,0.08)">${escapeHtml(title)}</div><div class="arena-panel-insight-item" style="color:#fca5a5;white-space:pre-wrap">${escapeHtml(message)}</div>`;
    body.appendChild(err);
    body.scrollTop = body.scrollHeight;
}

function addArenaRoundHeader(round, topic) {
    const body = document.getElementById('arenaPanelBody');
    const div = document.createElement('div');
    div.className = 'arena-live-round';
    div.id = `arena-round-${round}`;
    div.innerHTML = `<div class="arena-live-round-header">Round ${round} — ${escapeHtml(topic)}</div>`;
    body.appendChild(div);
    body.scrollTop = body.scrollHeight;
}

function addArenaAgentMessage(round, agentId, agentName, model, content) {
    const cfg = AGENT_CONFIG[agentId] || AGENT_CONFIG.analyst;
    const modelShort = model ? model.split(':')[0] : '';
    const roundEl = document.getElementById(`arena-round-${round}`);
    if (!roundEl) return;

    // Remove any typing indicator
    const typing = roundEl.querySelector('.arena-live-typing');
    if (typing) typing.remove();

    const div = document.createElement('div');
    div.className = 'arena-live-msg';
    div.style.setProperty('--agent-color', cfg.color);
    div.style.setProperty('--agent-glow', cfg.glow);
    div.innerHTML = `
        <div class="arena-live-avatar" style="border-color: ${cfg.color}; box-shadow: 0 0 12px ${cfg.glow}">${cfg.emoji}</div>
        <div class="arena-live-body">
            <div class="arena-live-header">
                <span class="arena-live-name" style="color: ${cfg.color}">${cfg.label}</span>
                <span class="arena-live-model">${escapeHtml(modelShort)}</span>
            </div>
            <div class="arena-live-text">${escapeHtml(content)}</div>
        </div>
    `;
    roundEl.appendChild(div);

    const body = document.getElementById('arenaPanelBody');
    body.scrollTop = body.scrollHeight;
}

function showArenaTyping(round, nextAgentName) {
    const roundEl = document.getElementById(`arena-round-${round}`);
    if (!roundEl) return;
    const existing = roundEl.querySelector('.arena-live-typing');
    if (existing) existing.remove();

    const div = document.createElement('div');
    div.className = 'arena-live-typing';
    div.innerHTML = `
        <div class="arena-live-typing-dots"><span></span><span></span><span></span></div>
        <span class="arena-live-typing-label">${escapeHtml(nextAgentName)} is thinking...</span>
    `;
    roundEl.appendChild(div);

    const body = document.getElementById('arenaPanelBody');
    body.scrollTop = body.scrollHeight;
}

function showArenaInsights(insights) {
    const el = document.getElementById('arenaPanelInsights');
    let html = '<div class="arena-panel-insights-title">💡 Key Insights</div>';
    for (const insight of insights) {
        html += `<div class="arena-panel-insight-item">• ${escapeHtml(insight)}</div>`;
    }
    el.innerHTML = html;
    el.className = 'arena-panel-insights active';
}

async function runArenaStreaming(message, thinkingId) {
    openArenaPanel();

    try {
        const response = await fetch(`${API_BASE}/brain/arena/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                history: chatHistory.slice(-10),
                conversation_id: conversationId
            })
        });

        if (!response.ok) {
            let detail = '';
            try {
                detail = (await response.text()).slice(0, 240);
            } catch (_err) {
                // Ignore response body parsing errors; status text is enough context.
            }
            throw new Error(`HTTP ${response.status} ${response.statusText}${detail ? ` — ${detail}` : ''}`);
        }

        if (!response.body) {
            throw new Error('Arena stream returned no response body.');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let currentRound = 0;
        let finalResponse = null;
        let lastAgentPairs = [];
        let streamError = null;
        let sawEvent = false;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const jsonStr = line.slice(6).trim();
                if (!jsonStr) continue;

                let event;
                try { event = JSON.parse(jsonStr); } catch(e) { continue; }
                sawEvent = true;

                switch (event.event) {
                    case 'plan':
                        updateArenaPanelStatus(`Planning: ${event.goals.length} goals`);
                        lastAgentPairs = event.agent_pairs || [];
                        break;

                    case 'round_start':
                        currentRound = event.round;
                        addArenaRoundHeader(event.round, event.topic);
                        updateArenaPanelStatus(`Round ${event.round}: ${event.topic}`);
                        if (event.agents && event.agents[0]) {
                            const cfg = AGENT_CONFIG[event.agents[0]];
                            showArenaTyping(event.round, cfg ? cfg.label : 'Agent');
                        }
                        break;

                    case 'agent_message':
                        addArenaAgentMessage(
                            event.round, event.agent_id, event.agent_name,
                            event.model, event.content
                        );
                        updateArenaPanelStatus(`${event.agent_name} spoke`);
                        // Show typing for next agent
                        showArenaTyping(event.round, 'Next agent');
                        break;

                    case 'observing':
                        // Remove last typing indicator
                        document.querySelectorAll('.arena-live-typing').forEach(e => e.remove());
                        updateArenaPanelStatus('Director observing...');
                        break;

                    case 'insights':
                        showArenaInsights(event.insights || []);
                        updateArenaPanelStatus('Insights extracted');
                        break;

                    case 'directing':
                        updateArenaPanelStatus('Director synthesizing final answer...');
                        document.getElementById('arenaPanel').classList.add('directing');
                        break;

                    case 'final':
                        finalResponse = event;
                        if (event.conversation_id) {
                            conversationId = event.conversation_id;
                        }
                        updateArenaPanelStatus('Complete');
                        break;

                    case 'error':
                        streamError = event.message || 'Unknown streaming error';
                        updateArenaPanelStatus('Error: ' + streamError);
                        addArenaPanelErrorCard(streamError);
                        break;

                    case 'done':
                        break;
                }
            }
        }

        if (!finalResponse && !streamError) {
            streamError = sawEvent
                ? 'Arena stream ended before a final response was produced.'
                : 'Arena stream returned no events.';
            updateArenaPanelStatus('Error: ' + streamError);
            addArenaPanelErrorCard(streamError, 'Incomplete Stream');
        }

        // Only auto-close when a final answer is actually produced.
        if (finalResponse) {
            await new Promise(r => setTimeout(r, 2000));
            closeArenaPanel();
            await new Promise(r => setTimeout(r, 700));
        }

        // Remove thinking indicator
        if (window.NeuralEffects) window.NeuralEffects.stopThinking();
        removeThinkingIndicator(thinkingId);

        if (finalResponse) {
            let responseContent = finalResponse.response;
            responseContent += `\n\n<em style="color: #fbbf24; font-size: 0.85em;">⚡ Arena: ${finalResponse.models_used ? finalResponse.models_used.length : '?'} models debated your question</em>`;

            addChatMessage('assistant', responseContent);
            chatHistory.push({ role: 'assistant', content: finalResponse.response });
        } else if (streamError) {
            addChatMessage('assistant', `Arena stream error: ${streamError}`);
        } else {
            addChatMessage('assistant', 'Arena completed but no final response was generated.');
        }

        updateStatus('🧠 Ready', 'success');

    } catch (error) {
        updateArenaPanelStatus('Error: ' + error.message);
        addArenaPanelErrorCard(error.message, 'Connection Error');
        if (window.NeuralEffects) window.NeuralEffects.stopThinking();
        removeThinkingIndicator(thinkingId);
        addChatMessage('assistant', 'Arena error: ' + error.message);
        updateStatus('❌ Arena error: ' + error.message, 'error');
    }
}
