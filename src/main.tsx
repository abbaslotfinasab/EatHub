import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './app/App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
      <div dir="rtl" className="w-full">
      <App />
      </div>
  </StrictMode>,
)
