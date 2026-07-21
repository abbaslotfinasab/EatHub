import {
    Grid,
} from "@mui/material";

import PeopleAltRoundedIcon from "@mui/icons-material/PeopleAltRounded";
import NorthEastRoundedIcon from "@mui/icons-material/NorthEastRounded";
import SouthWestRoundedIcon from "@mui/icons-material/SouthWestRounded";
import ShoppingBagRoundedIcon from "@mui/icons-material/ShoppingBagRounded";

import { StatCard } from "../common/StatCard";
import { formatCurrency } from "../../utils/formatCurrency";

interface CustomersStatsProps {
    totalCustomers: number;
    creditors: number;
    debtors: number;
    totalSpent: number;
}

export function CustomersStats({
    totalCustomers,
    creditors,
    debtors,
    totalSpent,
}: CustomersStatsProps) {

    const stats = [
        {
            title: "تعداد مشتریان",
            value: totalCustomers.toLocaleString(),
            subtitle: "مشتریان ثبت شده",
            icon: <PeopleAltRoundedIcon />,
            color: "#2563EB",
        },
        {
            title: "بستانکاری",
            value: formatCurrency(creditors),
            subtitle: "اعتبار نزد مشتریان",
            icon: <NorthEastRoundedIcon />,
            color: "#16A34A",
        },
        {
            title: "بدهکاری",
            value: formatCurrency(debtors),
            subtitle: "مطالبات قابل وصول",
            icon: <SouthWestRoundedIcon />,
            color: "#DC2626",
        },
        {
            title: "مجموع خرید",
            value: formatCurrency(totalSpent),
            subtitle: "خرید تمامی مشتریان",
            icon: <ShoppingBagRoundedIcon />,
            color: "#7C3AED",
        },
    ];

    return (
        <Grid
            container
            spacing={2.5}
        >
            {stats.map((item) => (
                <Grid
                    key={item.title}
                    size={{
                        xs: 12,
                        sm: 6,
                        lg: 3,
                    }}
                >
                    <StatCard
                        title={item.title}
                        value={item.value}
                        subtitle={item.subtitle}
                        icon={item.icon}
                        color={item.color}
                    />
                </Grid>
            ))}
        </Grid>
    );
}