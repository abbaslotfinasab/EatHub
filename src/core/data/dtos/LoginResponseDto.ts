export interface LoginResponseDto {
    access: string;
    refresh: string;
    user: {
        id: number;
        name: string;
        email: string;
        number: string;

    };
}