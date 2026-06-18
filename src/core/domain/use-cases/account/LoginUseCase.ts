// src/core/domain/usecases/LoginUseCase.ts


import type {Auth} from "../../entities/account/Auth.ts";
import type {AuthRepository} from "../../repositories/account/AuthRepository.ts";

export class LoginUseCase {
    constructor(
        private repo: AuthRepository
    ) {}

    async execute(
        email: string,
        password: string
    ): Promise<Auth> {
        return this.repo.login(email, password);
    }
}