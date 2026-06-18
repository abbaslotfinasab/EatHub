export interface HealthItem {
    title: string;
    status: "success" | "warning" | "error";
    primaryValue: string;
    secondaryValue: string;
}