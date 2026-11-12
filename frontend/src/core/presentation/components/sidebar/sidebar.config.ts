import DashboardRoundedIcon from "@mui/icons-material/DashboardRounded";
import ReceiptLongRoundedIcon from "@mui/icons-material/ReceiptLongRounded";
import RestaurantMenuRoundedIcon from "@mui/icons-material/RestaurantMenuRounded";
import PointOfSaleRoundedIcon from "@mui/icons-material/PointOfSaleRounded";
import Inventory2RoundedIcon from "@mui/icons-material/Inventory2Rounded";
import AssessmentRoundedIcon from "@mui/icons-material/AssessmentRounded";
import MenuBookRoundedIcon from "@mui/icons-material/MenuBookRounded";
import PeopleRoundedIcon from "@mui/icons-material/PeopleRounded";
import AlarmRoundedIcon from "@mui/icons-material/AlarmRounded";
import CategoryRoundedIcon from "@mui/icons-material/CategoryRounded";

import type { SidebarMenuItem } from "../../../domain/entities/account/SidebarMenuItem.ts";

export interface SidebarSectionConfig {
    title: string;
    items: SidebarMenuItem[];
}

export const dashboardItem: SidebarMenuItem = {
    title: "داشبورد",
    path: "/dashboard",
    icon: DashboardRoundedIcon,
};

export const sidebarSections: SidebarSectionConfig[] = [
    {
        title: "فروش",
        items: [
            { title: "سفارش ها", path: "/orders", icon: ReceiptLongRoundedIcon },
            { title: "محصولات", path: "/products", icon: CategoryRoundedIcon, requiredPermission: "products.view" },
            { title: "منو ها", path: "/menus", icon: RestaurantMenuRoundedIcon },
            {
                title: "رزرو ها",
                path: "/reserve",
                icon: AlarmRoundedIcon,
                comingSoonMessage: "این قابلیت در حال طراحی و توسعه است. پس از تکمیل فرایندهای ثبت، پیگیری و مدیریت رزروها، این بخش در دسترس شما قرار خواهد گرفت. از شکیبایی و همراهی شما سپاسگزاریم.",
            },
        ],
    },
    {
        title: "انبار",
        items: [
            { title: "موجودی", path: "/inventory", icon: AssessmentRoundedIcon },
            { title: "مواد اولیه", path: "/ingredients", icon: Inventory2RoundedIcon },
            {
                title: "مواد مرکب",
                path: "/materials",
                icon: Inventory2RoundedIcon,
                requiredPermission: "inventory.view",
            },
            { title: "رسپی‌ها", path: "/recipes", icon: MenuBookRoundedIcon },
        ],
    },
    {
        title: "خرید",
        items: [
            {
                title: "درخواست‌های خرید",
                path: "/purchase/requisitions",
                icon: ReceiptLongRoundedIcon,
                requiredPermission: "purchase.requisition.view_own",
            },
            {
                title: "سفارش‌های خرید",
                path: "/purchase/orders",
                icon: ReceiptLongRoundedIcon,
                requiredPermission: "purchase.view",
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
                comingSoonMessage: "بخش مدیریت فاکتورها در حال طراحی و توسعه است. پس از تکمیل فرایندهای ثبت، مشاهده و پیگیری فاکتورها، این قابلیت در دسترس شما قرار خواهد گرفت. از همراهی شما سپاسگزاریم.",
            },
        ],
    },
    {
        title: "مشتری",
        items: [
            { title: "کیف پول", path: "/customers", icon: PointOfSaleRoundedIcon },
        ],
    },
    {
        title: "کاربران",
        items: [
            {
                title: "کارمندان",
                path: "/users",
                icon: PeopleRoundedIcon,
                comingSoonMessage: "بخش مدیریت کارکنان در حال طراحی و توسعه است. پس از تکمیل فرایندهای دعوت، مدیریت دسترسی‌ها و پیگیری کارکنان، این قابلیت در دسترس شما قرار خواهد گرفت. از شکیبایی شما سپاسگزاریم.",
            },
        ],
    },
];
