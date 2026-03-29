/**
 * Hoffman Browser - Panel Preload
 * Bridges panel HTML to main process via contextBridge
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('hoffman', {
  analyzePage:    ()  => ipcRenderer.send('analyze-page'),
  getModelStatus: ()  => ipcRenderer.send('get-model-status'),
  loadModel:      ()  => ipcRenderer.send('load-model'),
  queryBmid: (domain, pattern) => ipcRenderer.invoke('query-bmid', domain, pattern),

  onPageChanged:      (cb) => ipcRenderer.on('page-changed',      (e, d) => cb(d)),
  onAnalysisStarted:  (cb) => ipcRenderer.on('analysis-started',  ()     => cb()),
  onAnalysisComplete: (cb) => ipcRenderer.on('analysis-complete', (e, d) => cb(d)),
  onAnalysisError:    (cb) => ipcRenderer.on('analysis-error',    (e, m) => cb(m)),
  onModelStatus:      (cb) => ipcRenderer.on('model-status',      (e, d) => cb(d)),
  onModelLoading:     (cb) => ipcRenderer.on('model-loading',     (e, d) => cb(d)),
  onModelReady:       (cb) => ipcRenderer.on('model-ready',       ()     => cb()),
  onModelError:       (cb) => ipcRenderer.on('model-error',       (e, m) => cb(m))
});
