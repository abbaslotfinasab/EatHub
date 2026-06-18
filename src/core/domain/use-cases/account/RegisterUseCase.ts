// domain/usecases/auth/RegisterUseCase.ts

import type { Auth } from "../../entities/account/Auth";
import type {AuthRepository} from "../../repositories/account/AuthRepository.ts";

export class RegisterUseCase {
    constructor(private repo: AuthRepository) {}

    async execute(
        email: string,
        password: string,
        name: string,
        number: string

    ): Promise<Auth> {
        return await this.repo.register(email, password,name,number);
    }
}