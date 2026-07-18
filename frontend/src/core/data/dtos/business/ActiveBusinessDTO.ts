export interface ActiveBusinessDTO {
    id: number;
    name: string;
    role: "OWNER" | "MANAGER" | "STAFF" | string;
    qr: string
    slug: string
}