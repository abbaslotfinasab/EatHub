// src/core/data/repositories/AuthRepositoryImpl.ts

import { AuthRemoteDataSource } from "../datasources/auth.remote";
import type {AuthRepository} from "../../domain/repositories/account/AuthRepository.ts";
import type {LoginRequestDto} from "../dtos/LoginRequestDto.ts";
import {authMapper} from "../mappers/authMapper.ts";
import type {Auth} from "../../domain/entities/account/Auth.ts";
import {meMapper} from "../mappers/meMapper.ts";
import type {RegisterRequestDto} from "../dtos/RegisterRequestDto.ts";
import type {Me} from "../../domain/entities/account/Me.ts";

export class AuthRepositoryImpl implements AuthRepository {
    constructor(
        private remote: AuthRemoteDataSource
    ) {}

    async register( email: string, password: string,name: string, number: string,): Promise<Auth> {
        const dto: RegisterRequestDto = {
            email,
            password,
            name,
            number,
        };
        const response =
            await this.remote.register(dto);

        return authMapper(response);

    }

    async me(): Promise<Me> {
        const response = await this.remote.me();

        return meMapper(response);
    }
    async login(
        identifier: string,
        password: string
    ): Promise<Auth> {

        const dto: LoginRequestDto = {
            identifier,
            password,
        };

        const response =
            await this.remote.login(dto);

        return authMapper(response);
    }
}