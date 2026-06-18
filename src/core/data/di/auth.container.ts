import {AuthRemoteDataSource} from "../datasources/auth.remote.ts";
import {AuthRepositoryImpl} from "../repositories/AuthRepositoryImpl.ts";
import {LoginUseCase} from "../../domain/use-cases/account/LoginUseCase.ts";
import {GetMeUseCase} from "../../domain/use-cases/account/GetMeUseCase.ts";
import {RegisterUseCase} from "../../domain/use-cases/account/RegisterUseCase.ts";


export const createAuthContainer = () => {
    const remote = new AuthRemoteDataSource();

    const repository = new AuthRepositoryImpl(remote);

    const loginUseCase = new LoginUseCase(repository);

    const registerUseCase = new RegisterUseCase(repository)

    const getMeUseCase = new GetMeUseCase(repository);

    return {
        loginUseCase,
        registerUseCase,
        getMeUseCase,
        repository,
    };
};