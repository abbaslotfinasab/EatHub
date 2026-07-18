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
let queue: ((token: string) => void)[] = [];

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
            return new Promise((resolve) => {
                queue.push((token: string) => {
                    originalRequest.headers.Authorization =
                        `Bearer ${token}`;
                    resolve(apiClient(originalRequest));
                });
            });
        }

        isRefreshing = true;

        try {
            const refreshToken =
                useAuthStore.getState().refreshToken;

            if (!refreshToken) {
                useAuthStore.getState().clear();
                return Promise.reject(new Error("No refresh token"));
            }

            const { data } = await axios.post(
                `${API_BASE_URL}/accounts/auth/refresh/`,
                {
                    refresh: refreshToken,
                }
            );

            const newAccessToken = data.access;

            // update store + localStorage
            useAuthStore
                .getState()
                .setTokens(
                    newAccessToken,
                    refreshToken
                );

            // retry queued requests
            queue.forEach((cb) =>
                cb(newAccessToken)
            );
            queue = [];

            // retry original request
            originalRequest.headers.Authorization =
                `Bearer ${newAccessToken}`;

            return apiClient(originalRequest);
        } catch (err) {
            // ❌ refresh fail → logout
            useAuthStore.getState().clear();

            return Promise.reject(err);
        } finally {
            isRefreshing = false;
        }
    }
);