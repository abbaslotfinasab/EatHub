// src/core/domain/models/Auth.ts

export interface Auth {
    userId: string;
    fullName: string;
    email: string;

    accessToken: string;
    refreshToken: string;
}