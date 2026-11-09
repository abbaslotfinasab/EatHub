import { create } from "zustand";

const STORAGE_KEY = "eathub.selectedBusinessId";

const readStoredBusinessId = (): number | null => {
    try {
        const value = sessionStorage.getItem(STORAGE_KEY);
        if (!value) return null;
        const id = Number(value);
        return Number.isSafeInteger(id) && id > 0 ? id : null;
    } catch {
        return null;
    }
};

let businessRequestController = new AbortController();

interface BusinessContextState {
    selectedBusinessId: number | null;
    selectBusiness: (businessId: number | null) => void;
    clearBusiness: () => void;
}

export const useBusinessContextStore = create<BusinessContextState>((set, get) => ({
    selectedBusinessId: readStoredBusinessId(),

    selectBusiness: (businessId) => {
        if (businessId !== null && (!Number.isSafeInteger(businessId) || businessId <= 0)) {
            throw new Error("Invalid business id");
        }
        if (get().selectedBusinessId === businessId) return;

        businessRequestController.abort();
        businessRequestController = new AbortController();

        try {
            if (businessId === null) sessionStorage.removeItem(STORAGE_KEY);
            else sessionStorage.setItem(STORAGE_KEY, String(businessId));
        } catch {
            // The in-memory tab context still works when sessionStorage is unavailable.
        }
        set({ selectedBusinessId: businessId });
    },

    clearBusiness: () => get().selectBusiness(null),
}));

export const getBusinessRequestSignal = () => businessRequestController.signal;
