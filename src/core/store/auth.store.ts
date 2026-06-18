import { create } from "zustand";
import type {Me} from "../domain/entities/account/Me.ts";


interface AuthStore {

    accessToken: string | null;

    refreshToken: string | null;

    me: Me | null;

    isHydrating: boolean;

    setMe: (me: Me) => void;

    setTokens: (a: string, r: string) => void;

    setHydrating: (value: boolean) => void;

    clear: () => void;
}

export const useAuthStore = create<AuthStore>((set) => ({

    accessToken: localStorage.getItem("accessToken"),

    refreshToken: localStorage.getItem("refreshToken"),

    me: null,

    isHydrating: true,

    setTokens: (a, r) => {
        localStorage.setItem("accessToken", a);
        localStorage.setItem("refreshToken", r);

        set({ accessToken: a, refreshToken: r });
    },

    setMe: (me) =>
        set({
            me,
        }),

    setHydrating: (value: boolean) =>
        set({
            isHydrating: value,
        }),

    clear: () => {
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");

        set({
            accessToken: null,
            refreshToken: null,
            me: null,
            isHydrating: false,
        });
    },
}));