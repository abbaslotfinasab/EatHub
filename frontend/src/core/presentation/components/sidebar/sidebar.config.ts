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

import AssessmentRoundedIcon
    from "@mui/icons-material/AssessmentRounded";

import AccountBalanceWalletRoundedIcon
    from "@mui/icons-material/AccountBalanceWalletRounded";

import MenuBookRoundedIcon from "@mui/icons-material/MenuBookRounded";

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
        title: "فروش",

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
                title: "موجودی",
                path: "/inventory",
                icon: AssessmentRoundedIcon,
            },

            {
                title: "مواد اولیه",
                path: "/ingredients",
                icon: Inventory2RoundedIcon,
            },
            {
                title: "مواد مرکب",
                path: "/materials",
                icon: Inventory2RoundedIcon,
                requiredPermission: "inventory.view",
            },

            {
                title: "رسپی‌ها",
                path: "/recipes",
                icon: MenuBookRoundedIcon,
            },

        ],
    },
    {
        title: "خرید",

        items: [

            {
                title: "سفارش‌های خرید",
                path: "/purchase/orders",
                icon: ReceiptLongRoundedIcon,
                requiredPermission: "purchase.view",
            },

             {
                title: "فاکتور ها",
                path: "/facture",
                icon: PointOfSaleRoundedIcon,
            },

            {
                title: "حسابداری",
                path: "/accounting",
                icon: AccountBalanceWalletRoundedIcon,
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
                title: "حسابداری",
                path: "/accounting",
                icon: AccountBalanceWalletRoundedIcon,
            },
        ],
    },

      {
        title: "مشتری",

        items: [

             {
                title: "کیف پول",
                path: "/customers",
                icon: PointOfSaleRoundedIcon,
            },

            {
                title: "حسابداری",
                path: "/accounting",
                icon: AccountBalanceWalletRoundedIcon,
            },
        ],
    },

    {
        title: "کاربران",

        items: [
            {
                title: "کارمندان",
                path: "/users",
                icon: PeopleRoundedIcon,
            },

            {
                title: "تنظیمات",
                path: "/settings",
                icon: SettingsRoundedIcon,
            },

             {
                title: "انبارها",
                path: "/warehouses",
                icon: WarehouseRoundedIcon,
            },
        ],
    },
];
