export interface Menu {
    id?: string;

    name: string;
    category: string;
    description: string | null;
    sortOrder: number;
    isActive: boolean;

    createdAt?: string;
    updatedAt?: string;
}