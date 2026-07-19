// src/core/presentation/components/sidebar/sidebar.config.ts

import DashboardRoundedIcon
    from "@mui/icons-material/DashboardRounded";

import ReceiptLongRoundedIcon
    from "@mui/icons-material/ReceiptLongRounded";

import RestaurantMenuRoundedIcon
    from "@mui/icons-material/RestaurantMenuRounded";

import PointOfSaleRoundedIcon
    from "@mui/icons-material/PointOfSaleRounded";

import Inventory2RoundedIcon
    from "@mui/icons-material/Inventory2Rounded";

import WarehouseRoundedIcon
    from "@mui/icons-material/WarehouseRounded";

import ShoppingCartRoundedIcon
    from "@mui/icons-material/ShoppingCartRounded";

import AssessmentRoundedIcon
    from "@mui/icons-material/AssessmentRounded";

import AccountBalanceWalletRoundedIcon
    from "@mui/icons-material/AccountBalanceWalletRounded";

import PeopleRoundedIcon
    from "@mui/icons-material/PeopleRounded";

import SettingsRoundedIcon
    from "@mui/icons-material/SettingsRounded";
import type {SidebarMenuItem} from "../../../domain/entities/account/SidebarMenuItem.ts";


// --------------------
// Types
// --------------------

export interface SidebarSectionConfig {
    title: string;

    items: SidebarMenuItem[];
}

// --------------------
// Dashboard
// --------------------

export const dashboardItem: SidebarMenuItem = {
    title: "داشبورد",
    path: "/dashboard",
    icon: DashboardRoundedIcon,
};

// --------------------
// Sections
// --------------------

export const sidebarSections: SidebarSectionConfig[] = [
    {
        title: "عملیات",

        items: [
            {
                title: "سفارش ها",
                path: "/orders",
                icon: ReceiptLongRoundedIcon,
            },

            {
                title: "منو ها",
                path: "/menus",
                icon: RestaurantMenuRoundedIcon,
            },

            {
                title: "رزرو ها",
                path: "/reserve",
                icon: PointOfSaleRoundedIcon,
            },
        ],
    },

    {
        title: "انبار",

        items: [
            {
                title: "مواد اولیه",
                path: "/ingredients",
                icon: Inventory2RoundedIcon,
            },

            {
                title: "مواد مرکب",
                path: "/warehouses",
                icon: WarehouseRoundedIcon,
            },

            {
                title: "رسپی ها",
                path: "/purchases",
                icon: ShoppingCartRoundedIcon,
            },
        ],
    },

    {
        title: "مالی",

        items: [

             {
                title: "فاکتور ها",
                path: "/facture",
                icon: PointOfSaleRoundedIcon,
            },

            {
                title: "کیف پول",
                path: "/wallet",
                icon: AssessmentRoundedIcon,
            },

            {
                title: "حسابداری",
                path: "/accounting",
                icon: AccountBalanceWalletRoundedIcon,
            },
        ],
    },

    {
        title: "مدیریت",

        items: [
            {
                title: "کاربران",
                path: "/users",
                icon: PeopleRoundedIcon,
            },

            {
                title: "تنظیمات",
                path: "/settings",
                icon: SettingsRoundedIcon,
            },
        ],
    },
];