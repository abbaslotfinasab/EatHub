export interface Business {
  id?: string;
  name: string;
  description?: string;
  phone: string;
  address?: string;
  logoUrl?: string | null;
  logo?: File | null;
}