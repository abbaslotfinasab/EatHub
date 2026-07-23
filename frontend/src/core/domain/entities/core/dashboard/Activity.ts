export interface Activity {

    id: number;

    title: string;

    description?: string;

    action: ActivityAction;

    user?: string;

    createdAt: string;
}


export type ActivityAction =
    | "create"
    | "update"
    | "delete"
    | "order_created"
    | "order_completed"
    | "order_cancelled"
    | "stock_low"
    | "login";