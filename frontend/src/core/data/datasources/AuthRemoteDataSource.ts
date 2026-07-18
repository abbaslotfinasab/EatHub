// src/core/data/datasources/AuthRemoteDataSource.ts



import {apiClient} from "../http/http-client.ts";
import type {LoginResponseDto} from "../dtos/auth/LoginResponseDto.ts";
import type {LoginRequestDto} from "../dtos/auth/LoginRequestDto.ts";
import type {MeResponseDto} from "../dtos/auth/MeResponseDto.ts";
import type {RegisterRequestDto} from "../dtos/auth/RegisterRequestDto.ts";

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