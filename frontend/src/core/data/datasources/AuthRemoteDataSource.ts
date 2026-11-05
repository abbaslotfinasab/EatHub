import {apiClient} from "../http/http-client.ts";
import type {LoginResponseDto} from "../dtos/auth/LoginResponseDto.ts";
import type {LoginRequestDto} from "../dtos/auth/LoginRequestDto.ts";
import type {MeResponseDto} from "../dtos/auth/MeResponseDto.ts";
import type {RegisterRequestDto} from "../dtos/auth/RegisterRequestDto.ts";

export class AuthRemoteDataSource {
    async register(dto: RegisterRequestDto): Promise<LoginResponseDto> {
        const {data} = await apiClient.post(
            "/accounts/auth/register/",
            dto,
        );
        return data;
    }

    async login(dto: LoginRequestDto): Promise<LoginResponseDto> {
        const {data} = await apiClient.post(
            "/accounts/auth/login/",
            dto,
        );
        return data;
    }

    async me(): Promise<MeResponseDto> {
        const {data} = await apiClient.get(
            "/accounts/auth/me/",
        );
        return data;
    }
}
