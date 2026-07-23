import type { DashboardRepository } from "../../../repositories/core/DashboardRepository";
import type {Dashboard} from "../../../entities/core/dashboard/Dashboard.ts";

export class GetDashboard {

    constructor(
        private readonly repository: DashboardRepository,
    ) {}

    async execute(): Promise<Dashboard> {
        return this.repository.getDashboard();
    }

}