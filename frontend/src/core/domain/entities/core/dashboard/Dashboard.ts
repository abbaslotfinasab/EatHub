import type { DashboardStats } from "./DashboardStats";
import type { SalesChartItem } from "./SalesChartItem";
import type {TopProduct} from "../../account/TopProduct.ts";
import type {OrderWithItems} from "../../product/order/OrderWithItems.ts";

export interface Dashboard {
    stats: DashboardStats;
    salesChart: SalesChartItem[];
    recentOrders: OrderWithItems[];
    topProducts: TopProduct[];
}