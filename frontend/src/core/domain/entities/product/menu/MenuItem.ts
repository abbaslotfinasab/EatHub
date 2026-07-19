export interface MenuItem {
    id?: number | null;
    menuId?: string;

    name: string;
    description: string | null;
    price: number;

    imageUrl: string | null;

    isAvailable: boolean | null;


    createdAt?: string;
    updatedAt?: string;
}