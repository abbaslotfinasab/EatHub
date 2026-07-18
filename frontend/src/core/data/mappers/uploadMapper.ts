import type { UploadResult } from "../../domain/repositories/core/UploadRepository";
import type {
    UploadFileResponseDTO,
} from "../dtos/upload/UploadFileResponseDTO";



export const uploadMapper = {


    toDomain(
        dto: UploadFileResponseDTO,
    ): UploadResult {


        return {

            url: dto.url,

            path: dto.path,

            filename: dto.filename,

            size: dto.size,

            contentType:
                dto.content_type,

        };

    },


};