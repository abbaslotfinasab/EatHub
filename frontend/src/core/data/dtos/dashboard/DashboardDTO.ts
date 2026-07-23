import type {DashboardStatsDTO} from "./DashboardStatsDTO";
import type {SalesChartItemDTO} from "./SalesChartItemDTO";
import type {TopProductDTO} from "./TopProductDTO";
import type {OrderDTO} from "../order/OrderDTO.ts";
import type { ActivityDTO } from "./ActivityDTO.ts";

export interface DashboardDTO {
    stats: DashboardStatsDTO;

    sales_chart: SalesChartItemDTO[];

    recent_orders: OrderDTO[];

    top_products: TopProductDTO[];

    activities: ActivityDTO[];


}