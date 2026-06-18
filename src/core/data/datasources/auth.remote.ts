// src/core/data/datasources/auth.remote.ts



import {apiClient} from "../http/http-client.ts";
import type {LoginResponseDto} from "../dtos/LoginResponseDto.ts";
import type {LoginRequestDto} from "../dtos/LoginRequestDto.ts";
import type {MeResponseDto} from "../dtos/MeResponseDto.ts";
import type {RegisterRequestDto} from "../dtos/RegisterRequestDto.ts";

export class AuthRemoteDataSource {

    async register(
        dto: RegisterRequestDto
    ): Promise<LoginResponseDto> {
        const { data } = await apiClient.post(
            "/accounts/auth/register/",
            dto
        );

        return data;

    }

    // =========================
    // LOGIN
    // =========================
    async login(
        dto: LoginRequestDto
    ): Promise<LoginResponseDto> {
        const { data } = await apiClient.post(
            "/accounts/auth/login/",
            dto
        );

        return data;
    }

    // =========================
    // REFRESH TOKEN
    // =========================
    async refresh(
        refreshToken: string
    ): Promise<{
        access: string;
        refresh?: string;
    }> {
        const { data } = await apiClient.post(
            "/auth/refresh/",
            {
                refreshToken,
            }
        );

        return data;
    }

    // =========================
    // GET CURRENT USER (/me)
    // =========================
    async me(): Promise<MeResponseDto> {
        const { data } = await apiClient.get(
            "/accounts/auth/me/"
        );

        return data;
    }

    // =========================
    // LOGOUT (optional backend call)
    // =========================
    async logout(): Promise<void> {
        await apiClient.post("/auth/logout/");
    }
}