import {apiClient} from "../http/http-client";
import type {BusinessRepository} from "../../domain/repositories/account/BusinessRepository.ts";
import type {Business} from "../../domain/entities/account/Business.ts";

export class BusinessRepositoryImpl implements BusinessRepository {
  async create(input: Business): Promise<void> {
    await apiClient.post("/accounts/create/business/", {
      name: input.name,
      number: input.phone,
      address: input.address ?? "",
      logo: input.logoUrl ?? null,
    });
  }
}