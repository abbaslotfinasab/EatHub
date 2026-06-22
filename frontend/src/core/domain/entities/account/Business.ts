// data/models/business/BusinessModel.ts

export interface Business {
  id?: string;

  name: string;

  phone: string;
  address?: string;

  logoUrl?: string ;

  logo?: File | null; // 👈 این فایل واقعیه

}