/**
 * UnifiedAi Brain Thinker - Neural Network Visual Effects
 * Deep purple neural connections, synaptic pulses, and brainwave patterns
 */

class NeuralNetwork {
    constructor() {
        this.neuralCanvas = document.getElementById('neuralCanvas');
        this.waveCanvas = document.getElementById('waveCanvas');
        
        if (!this.neuralCanvas || !this.waveCanvas) return;
        
        this.neuralCtx = this.neuralCanvas.getContext('2d');
        this.waveCtx = this.waveCanvas.getContext('2d');
        
        this.neurons = [];
        this.connections = [];
        this.pulses = [];
        this.waveOffset = 0;
        
        this.colors = {
            neuron: '#8b5cf6',
            neuronCore: '#a78bfa',
            connection: 'rgba(139, 92, 246, 0.15)',
            pulse: '#22d3ee',
            pulseFade: '#f472b6',
            wave1: 'rgba(139, 92, 246, 0.2)',
            wave2: 'rgba(34, 211, 238, 0.15)',
        };
        
        this.resize();
        this.init();
        this.animate();
        
        window.addEventListener('resize', () => this.resize());
    }
    
    resize() {
        const dpr = window.devicePixelRatio || 1;
        
        // Neural canvas
        this.neuralCanvas.width = window.innerWidth * dpr;
        this.neuralCanvas.height = window.innerHeight * dpr;
        this.neuralCanvas.style.width = `${window.innerWidth}px`;
        this.neuralCanvas.style.height = `${window.innerHeight}px`;
        this.neuralCtx.scale(dpr, dpr);
        
        // Wave canvas
        this.waveCanvas.width = window.innerWidth * dpr;
        this.waveCanvas.height = window.innerHeight * dpr;
        this.waveCanvas.style.width = `${window.innerWidth}px`;
        this.waveCanvas.style.height = `${window.innerHeight}px`;
        this.waveCtx.scale(dpr, dpr);
        
        this.width = window.innerWidth;
        this.height = window.innerHeight;
        
        // Reinitialize neurons when resizing
        if (this.neurons.length > 0) {
            this.init();
        }
    }
    
    init() {
        this.neurons = [];
        this.connections = [];
        
        // Create neurons scattered across the canvas
        const neuronCount = Math.floor((this.width * this.height) / 25000);
        
        for (let i = 0; i < neuronCount; i++) {
            this.neurons.push({
                x: Math.random() * this.width,
                y: Math.random() * this.height,
                vx: (Math.random() - 0.5) * 0.3,
                vy: (Math.random() - 0.5) * 0.3,
                radius: Math.random() * 2 + 1.5,
                pulsePhase: Math.random() * Math.PI * 2,
                active: false,
                activationTime: 0,
            });
        }
        
        // Create initial connections
        this.updateConnections();
    }
    
    updateConnections() {
        this.connections = [];
        const maxDistance = 150;
        
        for (let i = 0; i < this.neurons.length; i++) {
            for (let j = i + 1; j < this.neurons.length; j++) {
                const dx = this.neurons[i].x - this.neurons[j].x;
                const dy = this.neurons[i].y - this.neurons[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < maxDistance) {
                    this.connections.push({
                        from: i,
                        to: j,
                        distance,
                        opacity: 1 - distance / maxDistance,
                    });
                }
            }
        }
    }
    
    createPulse(fromNeuron, toNeuron) {
        this.pulses.push({
            fromX: fromNeuron.x,
            fromY: fromNeuron.y,
            toX: toNeuron.x,
            toY: toNeuron.y,
            progress: 0,
            speed: 0.02 + Math.random() * 0.02,
            color: Math.random() > 0.5 ? this.colors.pulse : this.colors.pulseFade,
        });
    }
    
    activateRandomNeuron() {
        if (Math.random() < 0.02 && this.neurons.length > 0) {
            const neuron = this.neurons[Math.floor(Math.random() * this.neurons.length)];
            neuron.active = true;
            neuron.activationTime = Date.now();
            
            // Find connected neurons and create pulses
            this.connections.forEach(conn => {
                const fromIdx = conn.from;
                const toIdx = conn.to;
                
                if (this.neurons[fromIdx] === neuron) {
                    this.createPulse(neuron, this.neurons[toIdx]);
                } else if (this.neurons[toIdx] === neuron) {
                    this.createPulse(neuron, this.neurons[fromIdx]);
                }
            });
        }
    }
    
    drawNeurons() {
        const ctx = this.neuralCtx;
        const time = Date.now() / 1000;
        
        this.neurons.forEach(neuron => {
            // Update position
            neuron.x += neuron.vx;
            neuron.y += neuron.vy;
            
            // Boundary wrapping
            if (neuron.x < 0) neuron.x = this.width;
            if (neuron.x > this.width) neuron.x = 0;
            if (neuron.y < 0) neuron.y = this.height;
            if (neuron.y > this.height) neuron.y = 0;
            
            // Calculate pulse effect
            const pulse = Math.sin(neuron.pulsePhase + time * 2) * 0.3 + 0.7;
            const isActive = neuron.active && (Date.now() - neuron.activationTime < 500);
            
            // Deactivate after pulse
            if (neuron.active && Date.now() - neuron.activationTime > 500) {
                neuron.active = false;
            }
            
            // Draw neuron glow
            const glowSize = neuron.radius * (isActive ? 8 : 4);
            const gradient = ctx.createRadialGradient(
                neuron.x, neuron.y, 0,
                neuron.x, neuron.y, glowSize
            );
            
            if (isActive) {
                gradient.addColorStop(0, 'rgba(34, 211, 238, 0.8)');
                gradient.addColorStop(0.3, 'rgba(139, 92, 246, 0.4)');
                gradient.addColorStop(1, 'transparent');
            } else {
                gradient.addColorStop(0, `rgba(139, 92, 246, ${0.5 * pulse})`);
                gradient.addColorStop(1, 'transparent');
            }
            
            ctx.beginPath();
            ctx.arc(neuron.x, neuron.y, glowSize, 0, Math.PI * 2);
            ctx.fillStyle = gradient;
            ctx.fill();
            
            // Draw neuron core
            ctx.beginPath();
            ctx.arc(neuron.x, neuron.y, neuron.radius * (isActive ? 1.5 : 1), 0, Math.PI * 2);
            ctx.fillStyle = isActive ? this.colors.pulse : this.colors.neuronCore;
            ctx.fill();
        });
    }
    
    drawConnections() {
        const ctx = this.neuralCtx;
        
        this.connections.forEach(conn => {
            const from = this.neurons[conn.from];
            const to = this.neurons[conn.to];
            
            // Recalculate distance for moving neurons
            const dx = from.x - to.x;
            const dy = from.y - to.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < 150) {
                const opacity = (1 - distance / 150) * 0.2;
                
                ctx.beginPath();
                ctx.moveTo(from.x, from.y);
                ctx.lineTo(to.x, to.y);
                ctx.strokeStyle = `rgba(139, 92, 246, ${opacity})`;
                ctx.lineWidth = 0.5;
                ctx.stroke();
            }
        });
    }
    
    drawPulses() {
        const ctx = this.neuralCtx;
        
        this.pulses = this.pulses.filter(pulse => {
            pulse.progress += pulse.speed;
            
            if (pulse.progress >= 1) return false;
            
            const x = pulse.fromX + (pulse.toX - pulse.fromX) * pulse.progress;
            const y = pulse.fromY + (pulse.toY - pulse.fromY) * pulse.progress;
            
            // Draw pulse glow
            const gradient = ctx.createRadialGradient(x, y, 0, x, y, 12);
            gradient.addColorStop(0, pulse.color);
            gradient.addColorStop(0.5, pulse.color.replace(')', ', 0.3)').replace('rgb', 'rgba'));
            gradient.addColorStop(1, 'transparent');
            
            ctx.beginPath();
            ctx.arc(x, y, 12, 0, Math.PI * 2);
            ctx.fillStyle = gradient;
            ctx.fill();
            
            // Draw pulse core
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, Math.PI * 2);
            ctx.fillStyle = pulse.color;
            ctx.fill();
            
            return true;
        });
    }
    
    drawBrainwaves() {
        const ctx = this.waveCtx;
        ctx.clearRect(0, 0, this.width, this.height);
        
        this.waveOffset += 0.015;
        
        const drawWave = (color, amplitude, frequency, yOffset, phase) => {
            ctx.beginPath();
            ctx.moveTo(0, this.height / 2 + yOffset);
            
            for (let x = 0; x <= this.width; x += 3) {
                const y = this.height / 2 + yOffset + 
                    Math.sin((x * frequency / this.width) * Math.PI * 2 + this.waveOffset + phase) * amplitude +
                    Math.sin((x * frequency * 2 / this.width) * Math.PI * 2 + this.waveOffset * 1.5) * (amplitude / 3);
                
                ctx.lineTo(x, y);
            }
            
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.stroke();
        };
        
        // Multiple brainwave layers
        drawWave(this.colors.wave1, 30, 3, -100, 0);
        drawWave(this.colors.wave2, 25, 4, -50, Math.PI / 4);
        drawWave(this.colors.wave1, 35, 2.5, 50, Math.PI / 2);
        drawWave(this.colors.wave2, 20, 5, 100, Math.PI);
    }
    
    animate() {
        // Clear neural canvas
        this.neuralCtx.fillStyle = 'rgba(5, 5, 16, 0.1)';
        this.neuralCtx.fillRect(0, 0, this.width, this.height);
        
        // Update connections periodically
        if (Math.random() < 0.01) {
            this.updateConnections();
        }
        
        // Random neuron activation
        this.activateRandomNeuron();
        
        // Draw elements
        this.drawConnections();
        this.drawPulses();
        this.drawNeurons();
        this.drawBrainwaves();
        
        requestAnimationFrame(() => this.animate());
    }
}

// Thinking particles effect - triggered when AI is processing
class ThinkingParticles {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;
        
        this.particles = [];
        this.isActive = false;
    }
    
    start() {
        this.isActive = true;
        this.emit();
    }
    
    stop() {
        this.isActive = false;
    }
    
    emit() {
        if (!this.isActive) return;
        
        const particle = document.createElement('div');
        particle.className = 'thinking-particle';
        particle.style.cssText = `
            position: absolute;
            width: 6px;
            height: 6px;
            background: linear-gradient(45deg, #8b5cf6, #22d3ee);
            border-radius: 50%;
            pointer-events: none;
            opacity: 0.8;
            left: ${Math.random() * 100}%;
            top: 100%;
            animation: particle-rise 2s ease-out forwards;
        `;
        
        this.container.appendChild(particle);
        
        setTimeout(() => particle.remove(), 2000);
        
        if (this.isActive) {
            setTimeout(() => this.emit(), 100 + Math.random() * 200);
        }
    }
}

// Add particle animation to styles dynamically
const particleStyles = document.createElement('style');
particleStyles.textContent = `
    @keyframes particle-rise {
        0% {
            transform: translateY(0) scale(1);
            opacity: 0.8;
        }
        100% {
            transform: translateY(-300px) scale(0);
            opacity: 0;
        }
    }
`;
document.head.appendChild(particleStyles);

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', () => {
    window.neuralNetwork = new NeuralNetwork();
    window.thinkingParticles = new ThinkingParticles('chatMessages');
});

// Export for use in app.js
window.NeuralEffects = {
    startThinking: () => window.thinkingParticles?.start(),
    stopThinking: () => window.thinkingParticles?.stop(),
};

