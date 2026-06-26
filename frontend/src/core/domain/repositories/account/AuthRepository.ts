// src/core/domain/repositories/AuthRepository.ts


import type {Auth} from "../../entities/account/Auth.ts";
import type {Me} from "../../entities/account/Me.ts";

export interface AuthRepository {
    login(
        identifier: string,
        password: string
    ): Promise<Auth>;

    me(): Promise<Me>;

    register(
        email: string,
        password: string,
        name: string,
        number: string
    ): Promise<Auth>;

}