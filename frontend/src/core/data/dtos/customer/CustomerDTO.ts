export interface CustomerDTO {
    id: number;

    business_id?: string;

    name: string;

    phone: string;

    balance?: number;

    totalOrders?: number;

    totalSpent?: string;

    user_id?: string | null;

    created_at?: string;
}