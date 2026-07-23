import type {DashboardRepository} from "../../domain/repositories/core/DashboardRepository";
import type {Dashboard} from "../../domain/entities/core/dashboard/Dashboard.ts";
import type {DashboardRemoteDataSource} from "../datasources/DashboardRemoteDataSource.ts";
import { dashboardMapper } from "../mappers/dashboardMapper.ts";

export class DashboardRepositoryImpl implements DashboardRepository {

    constructor(
        private readonly remoteDataSource: DashboardRemoteDataSource,
    ) {
    }

    async getDashboard(): Promise<Dashboard> {
        const dto = await this.remoteDataSource.getDashboard();

        return dashboardMapper.toDomain(dto);
    }

}