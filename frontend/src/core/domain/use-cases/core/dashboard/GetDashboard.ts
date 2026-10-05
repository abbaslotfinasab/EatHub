import type { DashboardRepository } from "../../../repositories/core/DashboardRepository";
import type {Dashboard} from "../../../entities/core/dashboard/Dashboard.ts";
import type {DashboardFilters} from "../../../objects/filters/DashboardFilters.ts";

export class GetDashboard {

    constructor(
        private readonly repository: DashboardRepository,
    ) {}

    async execute(filters?: DashboardFilters): Promise<Dashboard> {
        return this.repository.getDashboard(filters);
    }

}
