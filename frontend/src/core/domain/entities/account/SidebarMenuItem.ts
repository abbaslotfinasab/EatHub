import type { SvgIconComponent }
    from "@mui/icons-material";

export interface SidebarMenuItem {
    id?: string;
    title: string;
    icon: SvgIconComponent;
    path: string;
    badgeCount?:string,
    children?: SidebarMenuItem[];
}