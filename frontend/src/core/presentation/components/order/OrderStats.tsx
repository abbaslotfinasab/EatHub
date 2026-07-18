import ReceiptLongRoundedIcon from "@mui/icons-material/ReceiptLongRounded";
import ScheduleRoundedIcon from "@mui/icons-material/ScheduleRounded";
import SoupKitchenRoundedIcon from "@mui/icons-material/SoupKitchenRounded";
import PaymentsRoundedIcon from "@mui/icons-material/PaymentsRounded";

import {
    Grid,
} from "@mui/material";
import {StatCard} from "../dashboard/StatCard";

interface OrdersStatsProps {
    totalOrders: string;
    pendingOrders: string;
    preparingOrders: string;
    readyOrders: string;
}


export const OrdersStats = ({
                                totalOrders,
                                pendingOrders,
                                preparingOrders,
                                readyOrders,
                            }: OrdersStatsProps) => {
    return (
        <Grid container spacing={3}>

            <Grid
                key="کل سفارشات"
                size={{
                    xs: 12,
                    sm: 6,
                    lg: 3,
                }}
            >
                <StatCard
                    title="کل سفارشات"
                    color="#9333EA"
                    value={totalOrders}
                    icon={<ReceiptLongRoundedIcon/>}
                />

            </Grid>

            <Grid
                key="در انتظار"
                size={{
                    xs: 12,
                    sm: 6,
                    lg: 3,
                }}
            >
                <StatCard
                    title="در انتظار"
                    color="#9333EA"
                    value={pendingOrders}
                    icon={<ScheduleRoundedIcon/>}
                />
            </Grid>

            <Grid
                key="در حال آماده‌سازی"
                size={{
                    xs: 12,
                    sm: 6,
                    lg: 3,
                }}
            >
                <StatCard
                    title="در حال آماده‌سازی"
                    color="#9333EA"
                    value={preparingOrders}
                    icon={<SoupKitchenRoundedIcon/>}
                />
            </Grid>

            <Grid
                key="سفارشات آماده"
                size={{
                    xs: 12,
                    sm: 6,
                    lg: 3,
                }}
            >
                <StatCard
                    title="آماده"
                    color="#9333EA"
                    value={readyOrders}
                    icon={<PaymentsRoundedIcon/>}
                />
            </Grid>

        </Grid>
    );
};