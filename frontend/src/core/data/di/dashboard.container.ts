import { DashboardRemoteDataSource } from "../datasources/DashboardRemoteDataSource";
import { DashboardRepositoryImpl } from "../repositories/DashboardRepositoryImpl";

import { GetDashboard } from "../../domain/use-cases/core/dashboard/GetDashboard";

export const createDashboardContainer = () => {
    const remote = new DashboardRemoteDataSource();

    const repository = new DashboardRepositoryImpl(remote);

    return {
        getDashboardUseCase: new GetDashboard(repository),
    };
};