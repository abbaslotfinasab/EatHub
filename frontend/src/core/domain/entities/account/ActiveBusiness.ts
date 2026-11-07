export interface ActiveBusiness {
    id: number;
    name: string;
    role: string;
    slug? : string
    logo?: string | null;
    permissions: string[];
    inventory_enabled?: boolean;
}
