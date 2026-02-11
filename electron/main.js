const { app, BrowserWindow, Tray, Menu, shell, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn, spawnSync } = require('child_process');
const http = require('http');

let mainWindow;
let tray;
let pythonProcess;
const BACKEND_PORT = 10000;

function getIconPath() {
  const p = path.join(__dirname, 'icon.png');
  return fs.existsSync(p) ? p : null;
}
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`; // Use IPv4 explicitly

function getPythonRuntime() {
  if (process.platform !== 'win32') {
    return { command: 'python3', argsPrefix: [], label: 'python3' };
  }

  const userProfile = process.env.USERPROFILE || '';
  const appData = process.env.APPDATA || '';

  const directCandidates = [
    process.env.UNIFIEDAI_PYTHON,
    // Path user provided (often contains shortcuts; still check for python.exe)
    path.join(appData, 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Python 3.13', 'python.exe'),
    // Common real install locations
    path.join(userProfile, 'AppData', 'Local', 'Programs', 'Python', 'Python313', 'python.exe'),
    path.join(userProfile, 'AppData', 'Local', 'Programs', 'Python', 'Python311', 'python.exe'),
    'C:\\Python313\\python.exe',
    'C:\\Python314\\python.exe',
  ].filter(Boolean);

  for (const candidate of directCandidates) {
    if (candidate && fs.existsSync(candidate)) {
      return { command: candidate, argsPrefix: [], label: candidate };
    }
  }

  const launcherCandidates = [
    { command: 'py', argsPrefix: ['-3.13'], label: 'py -3.13' },
    { command: 'py', argsPrefix: [], label: 'py' },
    { command: 'python', argsPrefix: [], label: 'python' },
  ];

  for (const candidate of launcherCandidates) {
    const probe = spawnSync(candidate.command, [...candidate.argsPrefix, '--version'], {
      windowsHide: true,
      encoding: 'utf8',
      shell: true,
    });
    if (probe.status === 0) {
      return candidate;
    }
  }

  return null;
}

function ensureBackendDependencies(backendPath, pythonRuntime) {
  const checkScript = [
    'import importlib.util, sys',
    'mods=["uvicorn","fastapi","sqlalchemy","pydantic","httpx"]',
    'missing=[m for m in mods if importlib.util.find_spec(m) is None]',
    'print(",".join(missing))',
    'sys.exit(1 if missing else 0)',
  ].join(';');

  const check = spawnSync(
    pythonRuntime.command,
    [...pythonRuntime.argsPrefix, '-c', checkScript],
    {
      cwd: backendPath,
      windowsHide: true,
      encoding: 'utf8',
      shell: true,
    }
  );

  if (check.status === 0) {
    return true;
  }

  const missing = (check.stdout || '').trim() || 'unknown';
  console.log(`[UnifiedAi] Missing backend dependencies: ${missing}`);
  console.log('[UnifiedAi] Installing Python requirements...');

  const pipInstall = spawnSync(
    pythonRuntime.command,
    [...pythonRuntime.argsPrefix, '-m', 'pip', 'install', '-r', 'requirements.txt'],
    {
      cwd: backendPath,
      windowsHide: false,
      stdio: 'inherit',
      shell: true,
    }
  );

  return pipInstall.status === 0;
}

// Check if backend is ready
function checkBackend() {
  return new Promise((resolve) => {
    try {
      const req = http.get(`${BACKEND_URL}/health`, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          resolve(res.statusCode === 200);
        });
      });
      req.on('error', (err) => {
        console.log('[UnifiedAi] Backend check failed:', err.message);
        resolve(false);
      });
      req.setTimeout(2000, () => {
        req.destroy();
        resolve(false);
      });
    } catch (e) {
      resolve(false);
    }
  });
}

// Wait for backend to be ready
async function waitForBackend(maxAttempts = 30) {
  for (let i = 0; i < maxAttempts; i++) {
    if (await checkBackend()) {
      console.log('[UnifiedAi] Backend is ready!');
      return true;
    }
    console.log(`[UnifiedAi] Waiting for backend... (${i + 1}/${maxAttempts})`);
    await new Promise(r => setTimeout(r, 1000));
  }
  return false;
}

// Start the Python backend
function startBackend() {
  const isDev = !app.isPackaged;
  
  let backendPath;
  
  if (isDev) {
    // Development mode - use local paths
    backendPath = path.join(__dirname, '..', 'backend');
  } else {
    // Production mode - use resources
    backendPath = path.join(process.resourcesPath, 'backend');
  }

  console.log(`[UnifiedAi] Starting backend from: ${backendPath}`);
  const pythonRuntime = getPythonRuntime();
  if (!pythonRuntime) {
    dialog.showErrorBox(
      'Python Not Found',
      'Could not find a usable Python runtime.\n\n' +
      'Expected Python 3.13 path (or py/python in PATH):\n' +
      'C:\\Users\\AGrac\\AppData\\Local\\Programs\\Python\\Python313\\python.exe\n\n' +
      'You can also set UNIFIEDAI_PYTHON to your python.exe path.'
    );
    return;
  }

  console.log(`[UnifiedAi] Using Python runtime: ${pythonRuntime.label}`);

  const depsOk = ensureBackendDependencies(backendPath, pythonRuntime);
  if (!depsOk) {
    dialog.showErrorBox(
      'Backend Dependencies Failed',
      'Could not install backend dependencies.\n\n' +
      `Tried runtime: ${pythonRuntime.label}\n` +
      'Run manually:\n' +
      `cd "${backendPath}" && ${pythonRuntime.label} -m pip install -r requirements.txt`
    );
    return;
  }

  const args = [...pythonRuntime.argsPrefix, 'run.py'];

  pythonProcess = spawn(pythonRuntime.command, args, {
    cwd: backendPath,
    stdio: ['pipe', 'pipe', 'pipe'],
    shell: true,
    env: { ...process.env, PYTHONUNBUFFERED: '1' }
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    const msg = data.toString().trim();
    console.error(`[Backend Error] ${msg}`);
    // Keep last stderr for connection-failure dialog
    if (!pythonProcess._lastStderr) pythonProcess._lastStderr = [];
    pythonProcess._lastStderr.push(msg);
    if (pythonProcess._lastStderr.length > 10) pythonProcess._lastStderr.shift();
  });

  pythonProcess.on('error', (err) => {
    console.error('[UnifiedAi] Failed to start backend:', err);
    dialog.showErrorBox(
      'Backend Error',
        `Could not start Python backend.\n\n${err.message}\n\nInstall Python 3.13+ and run manually:\ncd backend && py -3.13 run.py`
    );
  });

  pythonProcess.on('close', (code, signal) => {
    console.log(`[UnifiedAi] Backend process exited with code ${code} signal ${signal}`);
    if (code !== 0 && code !== null) {
      const lastErr = (pythonProcess._lastStderr && pythonProcess._lastStderr.length)
        ? '\n\nLast output: ' + pythonProcess._lastStderr.slice(-3).join(' ')
        : '';
      dialog.showErrorBox(
        'Backend Crashed',
        `UnifiedAi backend exited (code: ${code}).${lastErr}\n\nTry running manually: cd backend && py -3.13 run.py`
      );
    }
  });
}

// Create the main window
function createWindow() {
  const iconPath = getIconPath();
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    title: 'UnifiedAi',
    ...(iconPath && { icon: iconPath }),
    backgroundColor: '#0a0a0f',
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  // Show loading screen first
  mainWindow.loadFile(path.join(__dirname, 'loading.html'));
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Wait for backend then load main app (give it 2s before first check)
  setTimeout(() => {
    waitForBackend().then((ready) => {
      if (ready) {
        mainWindow.loadURL(BACKEND_URL);
      } else {
        dialog.showErrorBox(
          'Connection Failed',
          'UnifiedAi backend did not start in time.\n\n' +
          '• Install Python 3.11+ from python.org (check "Add to PATH").\n' +
          '• From the UnifiedAi folder run: cd backend && py run.py\n' +
          '• Look for [Backend Error] in this console to see why.'
        );
      }
    });
  }, 2000);

  // Open external links in browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Create menu
  const menuTemplate = [
    {
      label: 'UnifiedAi',
      submenu: [
        { label: 'About', click: () => showAbout() },
        { type: 'separator' },
        { label: 'Reload', accelerator: 'CmdOrCtrl+R', click: () => mainWindow.reload() },
        { label: 'Dev Tools', accelerator: 'F12', click: () => mainWindow.webContents.toggleDevTools() },
        { type: 'separator' },
        { label: 'Quit', accelerator: 'CmdOrCtrl+Q', click: () => app.quit() }
      ]
    },
    {
      label: 'View',
      submenu: [
        { label: 'Zoom In', accelerator: 'CmdOrCtrl+Plus', click: () => mainWindow.webContents.setZoomLevel(mainWindow.webContents.getZoomLevel() + 0.5) },
        { label: 'Zoom Out', accelerator: 'CmdOrCtrl+-', click: () => mainWindow.webContents.setZoomLevel(mainWindow.webContents.getZoomLevel() - 0.5) },
        { label: 'Reset Zoom', accelerator: 'CmdOrCtrl+0', click: () => mainWindow.webContents.setZoomLevel(0) },
        { type: 'separator' },
        { label: 'Toggle Fullscreen', accelerator: 'F11', click: () => mainWindow.setFullScreen(!mainWindow.isFullScreen()) }
      ]
    }
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(menuTemplate));
}

// Show about dialog
function showAbout() {
  dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: 'About UnifiedAi',
    message: 'UnifiedAi',
    detail: 'The Ultimate Meta-Intelligence Platform\n\nVersion 1.0.0\n\nFeatures:\n• Meta-Intelligence Orchestrator\n• ActivatePrime Emotional AI\n• Knowledge Graph\n• Physics Simulation\n• Multi-Model Ensemble\n• And much more!'
  });
}

// Create system tray
function createTray() {
  // Tray icon (optional - skip if no icon file)
  try {
    const iconPath = getIconPath();
    if (!iconPath) return;
    tray = new Tray(iconPath);
    const contextMenu = Menu.buildFromTemplate([
      { label: 'Show UnifiedAi', click: () => mainWindow.show() },
      { type: 'separator' },
      { label: 'Quit', click: () => app.quit() }
    ]);
    tray.setToolTip('UnifiedAi');
    tray.setContextMenu(contextMenu);
    tray.on('click', () => mainWindow.show());
  } catch (e) {
    console.log('[UnifiedAi] No tray icon available');
  }
}

// App lifecycle
app.whenReady().then(async () => {
  console.log('[UnifiedAi] Starting application...');
  
  // Check if backend is already running (e.g., started manually)
  const alreadyRunning = await checkBackend();
  if (alreadyRunning) {
    console.log('[UnifiedAi] Backend already running, connecting...');
  } else {
    console.log('[UnifiedAi] Starting new backend instance...');
    startBackend();
  }
  
  createWindow();
  createTray();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  console.log('[UnifiedAi] Shutting down...');
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('[UnifiedAi] Uncaught exception:', error);
});

