// Insights Dashboard - Knowledge Graph & Analysis
// Enhanced meta-intelligence visualization

const INSIGHTS_API = 'http://localhost:10000/api/insights';

let knowledgeGraph = null;
let graphCanvas = null;
let graphCtx = null;
let graphNodes = [];
let graphEdges = [];
let graphStats = null;
let selectedNode = null;
let zoomLevel = 1.0;
let panOffset = { x: 0, y: 0 };
let isDragging = false;
let dragStart = { x: 0, y: 0 };
let insightStream = null;

// Initialize insights dashboard
function initInsightsDashboard() {
    graphCanvas = document.getElementById('graphCanvas');
    if (!graphCanvas) return;
    
    graphCtx = graphCanvas.getContext('2d');
    setupGraphCanvas();
    setupEventListeners();
    loadKnowledgeGraph();
    loadInsightStats();
}

function setupGraphCanvas() {
    if (!graphCanvas) return;
    
    // Set canvas size
    const container = graphCanvas.parentElement;
    graphCanvas.width = container.clientWidth;
    graphCanvas.height = Math.max(600, container.clientHeight);
    
    // Handle resize
    window.addEventListener('resize', () => {
        graphCanvas.width = container.clientWidth;
        graphCanvas.height = Math.max(600, container.clientHeight);
        renderGraph();
    });
    
    // Mouse events for interaction
    graphCanvas.addEventListener('mousedown', handleMouseDown);
    graphCanvas.addEventListener('mousemove', handleMouseMove);
    graphCanvas.addEventListener('mouseup', handleMouseUp);
    graphCanvas.addEventListener('wheel', handleWheel);
    graphCanvas.addEventListener('click', handleNodeClick);
}

function setupEventListeners() {
    // View toggle
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            switchView(view);
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
    
    // Filters
    document.getElementById('applyFilters')?.addEventListener('click', applyFilters);
    document.getElementById('refreshGraph')?.addEventListener('click', loadKnowledgeGraph);
    
    // Novelty/Testability sliders
    const noveltySlider = document.getElementById('noveltyFilter');
    const testabilitySlider = document.getElementById('testabilityFilter');
    
    if (noveltySlider) {
        noveltySlider.addEventListener('input', (e) => {
            document.getElementById('noveltyValue').textContent = e.target.value + '%';
        });
    }
    
    if (testabilitySlider) {
        testabilitySlider.addEventListener('input', (e) => {
            document.getElementById('testabilityValue').textContent = e.target.value + '%';
        });
    }
    
    // Graph controls
    document.getElementById('zoomIn')?.addEventListener('click', () => zoomGraph(1.2));
    document.getElementById('zoomOut')?.addEventListener('click', () => zoomGraph(0.8));
    document.getElementById('resetView')?.addEventListener('click', resetGraphView);
    document.getElementById('autoLayout')?.addEventListener('click', autoLayoutGraph);
    
    // Real-time streaming toggle
    document.getElementById('streamInsightsToggle')?.addEventListener('change', (e) => {
        if (e.target.checked) {
            startInsightStream();
        } else {
            stopInsightStream();
        }
    });
}

async function loadKnowledgeGraph() {
    try {
        updateStatus('🌐 Loading knowledge graph...', 'thinking');
        
        const response = await fetch(`${INSIGHTS_API}/knowledge-graph?limit=100`);
        
        if (!response.ok) {
            const errorText = await response.text();
            let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
            try {
                const errorJson = JSON.parse(errorText);
                errorMsg = errorJson.detail || errorMsg;
            } catch (e) {
                errorMsg = errorText || errorMsg;
            }
            throw new Error(errorMsg);
        }
        
        const data = await response.json();
        knowledgeGraph = data;
        graphNodes = data.nodes || [];
        graphEdges = data.edges || [];
        graphStats = data.stats || {};
        
        // Check if we have any insights
        if (graphNodes.length === 0) {
            updateStatus('ℹ️ No insights yet. Start the background mind to generate insights.', 'info');
            if (graphCanvas && graphCtx) {
                graphCtx.clearRect(0, 0, graphCanvas.width, graphCanvas.height);
                graphCtx.fillStyle = '#a0a0cc';
                graphCtx.font = '16px Space Grotesk';
                graphCtx.textAlign = 'center';
                graphCtx.fillText('No insights yet. Start the background mind!', graphCanvas.width / 2, graphCanvas.height / 2);
            }
            return;
        }
        
        // Update stats
        updateDashboardStats();
        
        // Auto layout
        autoLayoutGraph();
        
        // Render
        renderGraph();
        
        updateStatus(`✅ Knowledge graph loaded (${graphStats.total_insights} insights, ${graphStats.total_connections} connections)`, 'success');
    } catch (error) {
        console.error('Error loading graph:', error);
        const errorMsg = error.message || 'Unknown error';
        updateStatus('❌ Error loading graph: ' + errorMsg, 'error');
        
        // Show error on canvas if available
        if (graphCanvas && graphCtx) {
            graphCtx.clearRect(0, 0, graphCanvas.width, graphCanvas.height);
            graphCtx.fillStyle = '#f87171';
            graphCtx.font = '14px Space Grotesk';
            graphCtx.textAlign = 'center';
            graphCtx.fillText('Error loading graph:', graphCanvas.width / 2, graphCanvas.height / 2 - 20);
            graphCtx.fillText(errorMsg, graphCanvas.width / 2, graphCanvas.height / 2 + 10);
        }
    }
}

function updateDashboardStats() {
    if (!graphStats) return;
    
    document.getElementById('totalInsights').textContent = graphStats.total_insights || 0;
    document.getElementById('totalConnections').textContent = graphStats.total_connections || 0;
    document.getElementById('totalDomains').textContent = graphStats.total_domains || 0;
}

async function loadInsightStats() {
    try {
        const response = await fetch(`${INSIGHTS_API}/insights/stats`);
        if (!response.ok) return;
        
        const stats = await response.json();
        if (stats.avg_novelty) {
            document.getElementById('avgNovelty').textContent = 
                (stats.avg_novelty * 100).toFixed(0) + '%';
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function autoLayoutGraph() {
    if (!graphNodes.length) return;
    
    // Simple force-directed layout
    const centerX = graphCanvas.width / 2;
    const centerY = graphCanvas.height / 2;
    const radius = Math.min(graphCanvas.width, graphCanvas.height) * 0.3;
    
    // Position nodes in a circle initially
    graphNodes.forEach((node, i) => {
        if (node.type === 'insight') {
            const angle = (i * 2 * Math.PI) / graphNodes.filter(n => n.type === 'insight').length;
            node.x = centerX + radius * Math.cos(angle);
            node.y = centerY + radius * Math.sin(angle);
        } else if (node.type === 'domain') {
            // Position domain nodes around the edge
            const domainIndex = graphNodes.filter(n => n.type === 'domain').indexOf(node);
            const domainAngle = (domainIndex * 2 * Math.PI) / graphNodes.filter(n => n.type === 'domain').length;
            node.x = centerX + (radius * 1.5) * Math.cos(domainAngle);
            node.y = centerY + (radius * 1.5) * Math.sin(domainAngle);
        }
    });
    
    // Simple force-directed simulation (iterative)
    for (let iter = 0; iter < 50; iter++) {
        graphNodes.forEach(node => {
            if (!node.x || !node.y) {
                node.x = centerX + (Math.random() - 0.5) * radius;
                node.y = centerY + (Math.random() - 0.5) * radius;
            }
        });
        
        // Apply forces
        graphNodes.forEach(node1 => {
            let fx = 0, fy = 0;
            
            // Repulsion from other nodes
            graphNodes.forEach(node2 => {
                if (node1.id === node2.id) return;
                
                const dx = node1.x - node2.x;
                const dy = node1.y - node2.y;
                const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                const force = 1000 / (dist * dist);
                
                fx += (dx / dist) * force;
                fy += (dy / dist) * force;
            });
            
            // Attraction from connected nodes
            graphEdges.forEach(edge => {
                const source = graphNodes.find(n => n.id === edge.source);
                const target = graphNodes.find(n => n.id === edge.target);
                
                if (!source || !target || !source.x || !target.x || !source.y || !target.y) return;
                
                if (node1.id === edge.source) {
                    const dx = target.x - node1.x;
                    const dy = target.y - node1.y;
                    const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                    const force = dist * 0.01;
                    
                    fx += (dx / dist) * force;
                    fy += (dy / dist) * force;
                }
            });
            
            // Apply movement (damped)
            node1.vx = (node1.vx || 0) * 0.8 + fx * 0.1;
            node1.vy = (node1.vy || 0) * 0.8 + fy * 0.1;
            node1.x += node1.vx;
            node1.y += node1.vy;
        });
    }
    
    renderGraph();
}

function renderGraph() {
    if (!graphCtx || !graphCanvas) return;
    
    // Clear canvas
    graphCtx.clearRect(0, 0, graphCanvas.width, graphCanvas.height);
    
    // Apply zoom and pan
    graphCtx.save();
    graphCtx.translate(panOffset.x, panOffset.y);
    graphCtx.scale(zoomLevel, zoomLevel);
    
    // Draw edges first (so nodes appear on top)
    graphEdges.forEach(edge => {
        const source = graphNodes.find(n => n.id === edge.source);
        const target = graphNodes.find(n => n.id === edge.target);
        
        if (!source || !target || !source.x || !target.x || !source.y || !target.y) return;
        
        graphCtx.strokeStyle = `rgba(139, 92, 246, ${edge.strength * 0.5})`;
        graphCtx.lineWidth = edge.strength * 3;
        graphCtx.beginPath();
        graphCtx.moveTo(source.x, source.y);
        graphCtx.lineTo(target.x, target.y);
        graphCtx.stroke();
    });
    
    // Draw nodes
    graphNodes.forEach(node => {
        if (!node.x || !node.y) return;
        
        const isSelected = selectedNode?.id === node.id;
        const radius = node.type === 'domain' ? 20 : 15;
        
        // Node circle
        graphCtx.fillStyle = node.type === 'domain' 
            ? 'rgba(34, 211, 238, 0.8)' 
            : isSelected 
                ? 'rgba(139, 92, 246, 1)' 
                : 'rgba(139, 92, 246, 0.6)';
        
        graphCtx.beginPath();
        graphCtx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
        graphCtx.fill();
        
        // Glow effect for selected
        if (isSelected) {
            graphCtx.shadowBlur = 20;
            graphCtx.shadowColor = 'rgba(139, 92, 246, 0.8)';
            graphCtx.beginPath();
            graphCtx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
            graphCtx.fill();
            graphCtx.shadowBlur = 0;
        }
        
        // Label
        graphCtx.fillStyle = '#f0f0ff';
        graphCtx.font = '12px Space Grotesk';
        graphCtx.textAlign = 'center';
        const label = node.label || node.id;
        graphCtx.fillText(label.substring(0, 20), node.x, node.y + radius + 15);
    });
    
    graphCtx.restore();
}

function handleMouseDown(e) {
    isDragging = true;
    dragStart.x = e.clientX - panOffset.x;
    dragStart.y = e.clientY - panOffset.y;
}

function handleMouseMove(e) {
    if (isDragging) {
        panOffset.x = e.clientX - dragStart.x;
        panOffset.y = e.clientY - dragStart.y;
        renderGraph();
    }
}

function handleMouseUp() {
    isDragging = false;
}

function handleWheel(e) {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    zoomGraph(delta);
}

function handleNodeClick(e) {
    const rect = graphCanvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - panOffset.x) / zoomLevel;
    const y = (e.clientY - rect.top - panOffset.y) / zoomLevel;
    
    // Find clicked node
    selectedNode = null;
    graphNodes.forEach(node => {
        if (!node.x || !node.y) return;
        const dx = x - node.x;
        const dy = y - node.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const radius = node.type === 'domain' ? 20 : 15;
        
        if (dist < radius) {
            selectedNode = node;
        }
    });
    
    if (selectedNode) {
        showNodeDetails(selectedNode);
    }
    
    renderGraph();
}

function zoomGraph(factor) {
    zoomLevel = Math.max(0.5, Math.min(3.0, zoomLevel * factor));
    renderGraph();
}

function resetGraphView() {
    zoomLevel = 1.0;
    panOffset = { x: 0, y: 0 };
    renderGraph();
}

function switchView(view) {
    document.getElementById('knowledgeGraphView').classList.toggle('active', view === 'graph');
    document.getElementById('insightListView').classList.toggle('active', view === 'list');
    
    if (view === 'list') {
        loadInsightList();
    }
}

async function loadInsightList() {
    const container = document.getElementById('insightListContainer');
    container.innerHTML = '<p class="loading">Loading insights...</p>';
    
    try {
        const domain = document.getElementById('domainFilter')?.value || '';
        const minNovelty = (document.getElementById('noveltyFilter')?.value || 0) / 100;
        const minTestability = (document.getElementById('testabilityFilter')?.value || 0) / 100;
        
        const params = new URLSearchParams({
            limit: '50',
            min_novelty: minNovelty,
            min_testability: minTestability
        });
        if (domain) params.append('domain', domain);
        
        const response = await fetch(`${INSIGHTS_API}/insights?${params}`);
        if (!response.ok) throw new Error('Failed to load insights');
        
        const insights = await response.json();
        
        if (insights.length === 0) {
            container.innerHTML = '<p class="no-data">No insights match the filters.</p>';
            return;
        }
        
        container.innerHTML = insights.map(insight => `
            <div class="insight-card">
                <div class="insight-header">
                    <div class="insight-meta">
                        <span class="insight-time">${new Date(insight.timestamp).toLocaleString()}</span>
                        <div class="insight-badges">
                            ${insight.domains.map(d => `<span class="badge domain">${d}</span>`).join('')}
                            ${insight.tags.map(t => `<span class="badge tag">${t.name}</span>`).join('')}
                        </div>
                    </div>
                    <div class="insight-scores">
                        <span class="score novelty">Novelty: ${(insight.novelty_score * 100).toFixed(0)}%</span>
                        <span class="score testability">Testability: ${(insight.testability * 100).toFixed(0)}%</span>
                    </div>
                </div>
                <div class="insight-content">${insight.content}</div>
                ${insight.key_concepts.length > 0 ? `
                    <div class="insight-concepts">
                        <strong>Key Concepts:</strong> ${insight.key_concepts.join(', ')}
                    </div>
                ` : ''}
                ${insight.connections.length > 0 ? `
                    <div class="insight-connections">
                        <strong>Connections:</strong> ${insight.connections.length} related insights
                    </div>
                ` : ''}
            </div>
        `).join('');
    } catch (error) {
        container.innerHTML = `<p class="error">Error loading insights: ${error.message}</p>`;
    }
}

function applyFilters() {
    if (document.getElementById('insightListView').classList.contains('active')) {
        loadInsightList();
    } else {
        loadKnowledgeGraph();
    }
}

function showNodeDetails(node) {
    // Create a modal or sidebar to show node details
    console.log('Selected node:', node);
    // TODO: Implement node detail view
}

function startInsightStream() {
    if (insightStream) return;
    
    insightStream = new EventSource(`${INSIGHTS_API}/insights/stream`);
    
    insightStream.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'new_insight') {
            addStreamingInsight(data.insight);
        }
    };
    
    insightStream.onerror = (error) => {
        console.error('Stream error:', error);
        stopInsightStream();
    };
}

function stopInsightStream() {
    if (insightStream) {
        insightStream.close();
        insightStream = null;
    }
}

function addStreamingInsight(insight) {
    const insightsList = document.getElementById('insightsList');
    if (!insightsList) return;
    
    const insightDiv = document.createElement('div');
    insightDiv.className = 'insight-item streaming';
    insightDiv.innerHTML = `
        <div class="insight-time">${new Date(insight.timestamp).toLocaleString()}</div>
        <div class="insight-content">${insight.content}</div>
        <div class="insight-badges">
            ${insight.domains.map(d => `<span class="badge domain">${d}</span>`).join('')}
            ${insight.tags.map(t => `<span class="badge tag">${t}</span>`).join('')}
        </div>
    `;
    
    insightsList.insertBefore(insightDiv, insightsList.firstChild);
    
    // Remove old insights (keep last 20)
    while (insightsList.children.length > 20) {
        insightsList.removeChild(insightsList.lastChild);
    }
    
    // Animate in
    setTimeout(() => {
        insightDiv.classList.add('visible');
    }, 10);
}

// Export for use in app.js
if (typeof window !== 'undefined') {
    window.InsightsDashboard = {
        init: initInsightsDashboard,
        loadGraph: loadKnowledgeGraph,
        loadList: loadInsightList
    };
}

