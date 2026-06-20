// core/data/repositories/BusinessRepositoryImpl.ts



import { apiClient } from "../http/http-client";
import type {BusinessRepository} from "../../domain/repositories/account/BusinessRepository.ts";
import type {Business} from "../../domain/entities/account/Business.ts";

export class BusinessRepositoryImpl implements BusinessRepository {
  // 📌 CREATE BUSINESS
  async create(input: Business): Promise<void> {
    const formData = new FormData();

    formData.append("name", input.name);
    formData.append("number", input.phone);

    if (input.address) {
      formData.append("address", input.address);
    }

    if (input.logo) {
      formData.append("logo", input.logo);
    }

    await apiClient.post("/accounts/create/business/", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  }

}