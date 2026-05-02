

export const Unit = {
    INGREDIENT: 'Ingredient',
    MATERIAL: 'Material',
    RECIPE: 'Recipe',
    MENU: 'Menu',
} as const;

export type UnitType = typeof Unit[keyof typeof Unit];

export const UnitLabel: Record<UnitType, string> = {
    [Unit.INGREDIENT]: 'انبار',
    [Unit.MATERIAL]: 'مواد اولیه',
    [Unit.RECIPE]: 'رسپی',
    [Unit.MENU]: 'منو',
};


export interface Category {
    id?: string;
    name: string;
    unit: UnitType;
    isActive?: boolean;
    createdAt?: string;         // ISO
    updatedAt?: string;
}
