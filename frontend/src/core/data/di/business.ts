import {CreateBusiness} from "../../domain/use-cases/account/business/CreateBusinessUseCase.ts";
import {BusinessRepositoryImpl} from "../repositories/BusinessRepositoryImpl.ts";


// اگر بعداً اضافه کردی:
// import { UpdateBusiness } from "../../domain/use-cases/business/UpdateBusiness";

const businessRepository = new BusinessRepositoryImpl();

// 📌 UseCase instances (Dependency Injection)

export const createBusinessUseCase = new CreateBusiness(businessRepository);
