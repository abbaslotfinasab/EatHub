export interface ActiveBusiness {
    id: number;
    name: string;
    role: string;
    slug? : string
    permissions: string[];
    inventory_enabled?: boolean;
}
