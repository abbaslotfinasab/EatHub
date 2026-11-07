export interface ActiveBusinessDTO {
    id: number;
    name: string;
    role: "OWNER" | "MANAGER" | "STAFF" | string;
    slug: string
    permissions?: string[] | null;
    inventory_enabled?: boolean;
}
