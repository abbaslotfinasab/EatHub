export interface CustomerDTO {
    id: string;
    business_id?: string;

    name: string;
    phone: string;

    balance?: number;
    totalOrders?: number;
    totalSpent?: number;

    user_id?: string | null;

    created_at?: string;
}