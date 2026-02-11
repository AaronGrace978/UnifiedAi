// Preload script - runs before web content loads
// Provides secure bridge between renderer and main process

const { contextBridge, ipcRenderer } = require('electron');

// Expose safe APIs to the renderer
contextBridge.exposeInMainWorld('electronAPI', {
  // App info
  isElectron: true,
  platform: process.platform,
  
  // Window controls (if needed)
  minimize: () => ipcRenderer.send('window-minimize'),
  maximize: () => ipcRenderer.send('window-maximize'),
  close: () => ipcRenderer.send('window-close'),
  
  // Notifications
  notify: (title, body) => {
    new Notification(title, { body });
  }
});

console.log('[UnifiedAi] Preload script loaded');

