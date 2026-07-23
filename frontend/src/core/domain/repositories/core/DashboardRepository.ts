import type { Dashboard } from "../../entities/core/dashboard/Dashboard";

export interface DashboardRepository {
    getDashboard(): Promise<Dashboard>;
}