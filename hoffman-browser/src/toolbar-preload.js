/**
 * Hoffman Browser - Toolbar Preload
 * Bridges toolbar HTML to main process via contextBridge
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('hoffman', {
  navigate:    (url)  => ipcRenderer.send('navigate', url),
  goBack:      ()     => ipcRenderer.send('go-back'),
  goForward:   ()     => ipcRenderer.send('go-forward'),
  reload:      ()     => ipcRenderer.send('reload'),
  togglePanel: ()     => ipcRenderer.send('toggle-panel'),

  onUrlChanged:   (cb) => ipcRenderer.on('url-changed',   (e, url)   => cb(url)),
  onTitleChanged: (cb) => ipcRenderer.on('title-changed', (e, title) => cb(title)),
  onLoading:      (cb) => ipcRenderer.on('loading',       (e, v)     => cb(v)),
  onPanelState:   (cb) => ipcRenderer.on('panel-state',   (e, v)     => cb(v))
});
