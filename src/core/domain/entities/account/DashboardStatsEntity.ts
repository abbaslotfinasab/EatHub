export interface DashboardStat {
    title: string;
    value: string;
    subtitle?: string;
    growth?: number;
    icon: React.ReactNode;
    color: string;
}