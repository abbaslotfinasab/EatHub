// domain/entities/customer/CustomerListItem.ts

export interface CustomerListItem {
    id: number;

    name: string;

    phone: string;

    balance?: number;

    totalOrders?: number;

    totalSpent?: number;

    createdAt?: string;
}