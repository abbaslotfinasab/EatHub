// src/core/data/mappers/auth.mapper.ts


import type {LoginResponseDto} from "../dtos/auth/LoginResponseDto.ts";
import type {Auth} from "../../domain/entities/account/Auth.ts";

export const authMapper = (
    dto: LoginResponseDto
): Auth => {
    return {
        userId: dto.user.id.toString(),
        fullName: dto.user.name,
        email: dto.user.email,

        accessToken: dto.access,
        refreshToken: dto.refresh,
    };
};