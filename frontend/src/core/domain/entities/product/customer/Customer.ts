// domain/entities/customer/Customer.ts

export interface Customer {
    id?: number;

    name: string;

    phone: string;

    totalOrders?: number;

    totalSpent?: number;

    userId?: string | null;

    createdAt?: string;
}