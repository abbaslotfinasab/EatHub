// src/core/data/http-client.ts
import axios from 'axios';
import { API_BASE_URL } from '../../../config/constants';

// یک نمونه Axios سفارشی برای تمام پروژه بسازید
export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000, // زمان انتظار برای هر درخواست (۱۰ ثانیه)
    headers: {
        'Content-Type': 'application/json',
    },
});

// ✅ Request Interceptor: قبل از ارسال هر درخواست اجرا می‌شود
apiClient.interceptors.request.use(
    (config) => {
        // اضافه کردن توکن احراز هویت به هدر درخواست
        const token = localStorage.getItem('accessToken');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// ✅ Response Interceptor: پس از دریافت پاسخ اجرا می‌شود
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // اگر خطای ۴۰۱ (Unauthorized) دریافت کردیم و قبلاً برای رفرش تلاش نکرده بودیم
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                // درخواست برای گرفتن توکن جدید
                const refreshToken = localStorage.getItem('refreshToken');
                const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                    refreshToken,
                });

                const { accessToken } = response.data;
                localStorage.setItem('accessToken', accessToken);
                // هدر درخواست اصلی را به‌روز کرده و دوباره آن را ارسال می‌کنیم
                originalRequest.headers.Authorization = `Bearer ${accessToken}`;
                return apiClient(originalRequest);
            } catch (refreshError) {
                // اگر رفرش توکن هم معتبر نبود، کاربر را به صفحه ورود هدایت کنید
                localStorage.removeItem('accessToken');
                localStorage.removeItem('refreshToken');
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }
        return Promise.reject(error);
    }
);