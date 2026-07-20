export interface CustomerDTO {
    id: number;

    business_id?: string;

    name: string;

    phone: string;

    balance?: string;

    totalOrders?: number;

    totalSpent?: string;

    user_id?: string | null;

    created_at?: string;
}