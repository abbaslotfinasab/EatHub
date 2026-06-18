// src/core/domain/usecases/GetMeUseCase.ts


import type {AuthRepository} from "../../repositories/account/AuthRepository.ts";
import type {Me} from "../../entities/account/Me.ts";

export class GetMeUseCase {
    constructor(
        private repo: AuthRepository
    ) {}

    async execute(): Promise<Me> {
        return this.repo.me();
    }
}