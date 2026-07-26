// domain/entities/customer/Customer.ts

export interface Customer {
    id?: number;

    name: string;

    phone: string;

    userId?: string | null;

    createdAt?: string;
}