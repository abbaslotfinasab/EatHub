import type {Dashboard} from "../../domain/entities/core/dashboard/Dashboard";

import type {DashboardDTO} from "../dtos/dashboard/DashboardDTO";
import type {DashboardStatsDTO} from "../dtos/dashboard/DashboardStatsDTO";
import type {SalesChartItemDTO} from "../dtos/dashboard/SalesChartItemDTO";
import type {TopProductDTO} from "../dtos/dashboard/TopProductDTO";

import {orderMapper} from "./orderMapper";
import {activityMapper} from "./activityMapper.ts";

export const dashboardMapper = {

    // =====================================================
    // DTO -> DOMAIN
    // =====================================================

    toDomain(dto: DashboardDTO): Dashboard {
        return {
            stats: dashboardMapper.toStats(dto.stats),
            salesChart: dto.sales_chart.map(dashboardMapper.toSalesChartItem),
            recentOrders: dto.recent_orders.map(orderMapper.toDomain),
            topProducts: dto.top_products.map(dashboardMapper.toTopProduct),
            activities:
                activityMapper.toDomainList(
                    dto.activities
                ),
        };
    },

    toStats(dto: DashboardStatsDTO) {
        return {
            todaySales: Number(dto.today_sales),
            todayOrders: dto.today_orders,
            activeOrders: dto.active_orders,
            todayReservations: dto.today_reservations,
            inventoryAlerts: dto.inventory_alerts,
        };
    },

    toSalesChartItem(dto: SalesChartItemDTO) {
        return {
            date: dto.date,
            sales: dto.sales,
        };
    },

    toTopProduct(dto: TopProductDTO) {
        return {
            menuItemId: dto.menu_item_id,
            name: dto.name,
            totalSold: dto.total_sold,
            revenue: dto.revenue,
        };
    },

};