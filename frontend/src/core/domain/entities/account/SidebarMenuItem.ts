import type { SvgIconComponent }
    from "@mui/icons-material";

export interface SidebarMenuItem {
    id?: string;
    title: string;
    icon: SvgIconComponent;
    path: string;
    requiredPermission?: string;
    badgeCount?:string,
    comingSoonMessage?: string;
    children?: SidebarMenuItem[];
}
