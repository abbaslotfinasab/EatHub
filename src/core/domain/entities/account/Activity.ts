export interface Activity {
    id: string;

    userName: string;

    action: string;

    timestamp: string;

    type:
        | "order"
        | "inventory"
        | "accounting"
        | "reservation"
        | "menu";
}