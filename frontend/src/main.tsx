import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { CssBaseline, ThemeProvider } from "@mui/material";

import "./index.css";
import App from "./app/App";


import { NavbarProvider } from "./core/presentation/providers/NavbarProvider";
import { SidebarProvider } from "./core/presentation/providers/SidebarProvider";
import { theme } from "./core/presentation/theme/theme";

createRoot(document.getElementById("root")!).render(
    <StrictMode>
        <ThemeProvider theme={theme}>
            <CssBaseline />

            <NavbarProvider>
                <SidebarProvider>
                    <div dir="rtl" className="w-full">
                        <App />
                    </div>
                </SidebarProvider>
            </NavbarProvider>

        </ThemeProvider>
    </StrictMode>
);