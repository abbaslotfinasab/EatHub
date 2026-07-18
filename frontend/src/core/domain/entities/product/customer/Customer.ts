// domain/entities/customer/Customer.ts

export interface Customer {
    id?: string;

    name: string;

    phone: string;

    userId?: string | null;

    createdAt?: string;
}