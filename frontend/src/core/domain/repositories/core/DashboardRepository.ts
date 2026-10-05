import type { Dashboard } from "../../entities/core/dashboard/Dashboard";
import type {DashboardFilters} from "../../objects/filters/DashboardFilters.ts";

export interface DashboardRepository {
    getDashboard(filters?: DashboardFilters): Promise<Dashboard>;
}
