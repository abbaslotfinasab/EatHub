// domain/repositories/business/BusinessRepository.ts


import type {Business} from "../../entities/account/Business.ts";

export interface BusinessRepository {

  create(input: Business): Promise<void>;

}