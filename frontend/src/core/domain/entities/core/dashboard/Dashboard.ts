import type {DashboardStats} from "./DashboardStats";
import type {SalesChartItem} from "./SalesChartItem";
import type {TopProduct} from "../../account/TopProduct.ts";
import type {OrderWithItems} from "../../product/order/OrderWithItems.ts";
import type {Activity} from "./Activity.ts";
import type {PaginatedResult} from "../../../objects/PaginatedResult.ts";

export interface Dashboard {
    stats: DashboardStats;
    salesChart: SalesChartItem[];
    recentOrders: PaginatedResult<OrderWithItems>;
    topProducts: TopProduct[];
    activities: Activity[];

}
