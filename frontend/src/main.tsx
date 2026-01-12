import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// 抑制浏览器扩展引起的错误（不影响应用功能）
window.addEventListener('error', (event) => {
  if (
    event.message?.includes('message channel closed') ||
    event.message?.includes('asynchronous response')
  ) {
    event.preventDefault();
    return false;
  }
});

window.addEventListener('unhandledrejection', (event) => {
  if (
    event.reason?.message?.includes('message channel closed') ||
    event.reason?.message?.includes('asynchronous response')
  ) {
    event.preventDefault();
    return false;
  }
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

