import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import './index.css'
import App from './app/App'

import { NavbarProvider } from './core/presentation/providers/NavbarProvider'
import { SidebarProvider } from './core/presentation/providers/SidebarProvider'

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <NavbarProvider>
            <SidebarProvider>
                <div dir="rtl" className="w-full">
                    <App />
                </div>
            </SidebarProvider>
        </NavbarProvider>
    </StrictMode>,
)