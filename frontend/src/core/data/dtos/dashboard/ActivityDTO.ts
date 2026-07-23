export interface ActivityDTO {

    id: number;

    title: string;

    description?: string | null;

    action: string;

    user?: string | null;

    created_at: string;
}