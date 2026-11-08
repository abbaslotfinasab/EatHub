// src/core/data/http-client.ts
import axios from "axios";
import { API_BASE_URL } from "../../../config/constants";
import { useAuthStore } from "../../presentation/store/auth.store";
import { getBusinessRequestSignal, useBusinessContextStore } from "../../presentation/store/business-context.store";

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15000,
    headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
    },
});

apiClient.interceptors.request.use(
    (config) => {
        const token = useAuthStore.getState().accessToken;
        const businessId = useBusinessContextStore.getState().selectedBusinessId;

        if (token) config.headers.Authorization = `Bearer ${token}`;
        if (businessId !== null) config.headers["X-Business-Id"] = String(businessId);

        // Requests started under an old business context are cancelled on switch.
        if (!config.signal) config.signal = getBusinessRequestSignal();
        return config;
    },
    (error) => Promise.reject(error)
);

let isRefreshing = false;
let queue: Array<{
    resolve: (token: string) => void;
    reject: (error: unknown) => void;
}> = [];

apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        if (
            axios.isCancel(error) ||
            error.code === "ERR_CANCELED" ||
            error.response?.status !== 401 ||
            originalRequest?._retry
        ) {
            return Promise.reject(error);
        }
        if (!originalRequest) return Promise.reject(error);

        originalRequest._retry = true;
        if (isRefreshing) {
            return new Promise((resolve, reject) => {
                queue.push({
                    resolve: (token: string) => {
                        originalRequest.headers.Authorization = `Bearer ${token}`;
                        resolve(apiClient(originalRequest));
                    },
                    reject,
                });
            });
        }

        isRefreshing = true;
        try {
            const refreshToken = useAuthStore.getState().refreshToken;
            if (!refreshToken) throw new Error("No refresh token");

            const { data } = await axios.post(
                `${API_BASE_URL}/accounts/auth/refresh/`,
                { refresh: refreshToken },
            );
            const newAccessToken = data.access;
            const newRefreshToken = data.refresh ?? refreshToken;
            useAuthStore.getState().setTokens(newAccessToken, newRefreshToken);

            queue.forEach((waiter) => waiter.resolve(newAccessToken));
            queue = [];
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            return apiClient(originalRequest);
        } catch (err) {
            queue.forEach((waiter) => waiter.reject(err));
            queue = [];
            useAuthStore.getState().clear();
            return Promise.reject(err);
        } finally {
            isRefreshing = false;
        }
    }
);
