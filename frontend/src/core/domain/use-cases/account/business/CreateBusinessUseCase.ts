// domain/use-cases/business/CreateBusiness.ts

import { z } from "zod";
import type {BusinessRepository} from "../../../repositories/account/BusinessRepository.ts";

// اگر enum داری بعداً اینجا اضافه کن
// import { BusinessType } from "../../../entities/business/Business";

export const CreateBusinessSchema = z.object({
  name: z
    .string()
    .min(3, "نام کسب‌وکار حداقل ۳ کاراکتر است")
    .trim(),

  phone: z.string().min(8, "شماره تماس معتبر نیست").trim(),

  address: z.string().optional(),

  logo: z.any().nullable().optional(), // File | null
});

export type CreateBusinessInput = z.infer<typeof CreateBusinessSchema>;

export class CreateBusiness {
  constructor(private businessRepository: BusinessRepository) {}

  async execute(input: CreateBusinessInput): Promise<void> {
    // ✅ validation مثل Ingredient
    const validated = CreateBusinessSchema.parse(input);

    // 📡 ارسال به repository (POST به backend)
    await this.businessRepository.create(validated);
  }
}