// src/core/data/http-client.ts
import axios from "axios";
import { API_BASE_URL } from "../../../config/constants";
import { useAuthStore } from "../../presentation/store/auth.store";

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
        const token =
            useAuthStore.getState().accessToken;

        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

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
            error.response?.status !== 401 ||
            originalRequest._retry
        ) {
            return Promise.reject(error);
        }

        originalRequest._retry = true;

        // اگر refresh در حال انجام است → صف
        if (isRefreshing) {
            return new Promise((resolve, reject) => {
                queue.push({
                    resolve: (token: string) => {
                        originalRequest.headers.Authorization =
                            `Bearer ${token}`;
                        resolve(apiClient(originalRequest));
                    },
                    reject,
                });
            });
        }

        isRefreshing = true;

        try {
            const refreshToken =
                useAuthStore.getState().refreshToken;

            if (!refreshToken) {
                throw new Error("No refresh token");
            }

            const { data } = await axios.post(
                `${API_BASE_URL}/accounts/auth/refresh/`,
                {
                    refresh: refreshToken,
                }
            );

            const newAccessToken = data.access;
            const newRefreshToken = data.refresh ?? refreshToken;

            // SimpleJWT rotates refresh tokens when ROTATE_REFRESH_TOKENS is enabled.
            // Persist the rotated token or the next refresh attempt will be rejected.
            useAuthStore
                .getState()
                .setTokens(newAccessToken, newRefreshToken);

            // Retry queued requests only after both tokens have been persisted.
            queue.forEach((waiter) =>
                waiter.resolve(newAccessToken)
            );
            queue = [];

            // retry original request
            originalRequest.headers.Authorization =
                `Bearer ${newAccessToken}`;

            return apiClient(originalRequest);
        } catch (err) {
            // Reject every request waiting for the refresh attempt; never leave
            // requests pending forever when refresh fails.
            queue.forEach((waiter) => waiter.reject(err));
            queue = [];

            // A failed refresh invalidates the local authenticated session.
            useAuthStore.getState().clear();

            return Promise.reject(err);
        } finally {
            isRefreshing = false;
        }
    }
);