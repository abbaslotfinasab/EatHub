// src/core/presentation/contexts/NavbarContext.ts
import { createContext } from 'react';
import type {NavbarContextType} from "../providers/NavbarProvider.tsx";

export const NavbarContext = createContext<NavbarContextType | undefined>(undefined);