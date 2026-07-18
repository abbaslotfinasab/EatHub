export interface MenuItem {
    id?: string;
    menuId?: string;

    name: string;
    description: string | null;
    price: number;

    imageUrl: string | null;

    isAvailable: boolean;


    createdAt?: string;
    updatedAt?: string;
}