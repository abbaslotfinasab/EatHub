import type {UploadOptions, UploadRepository, UploadResult} from "../../domain/repositories/core/UploadRepository";
import {
    UploadRemoteDataSource,
} from "../datasources/UploadRemoteDataSource";
import {uploadMapper} from "../mappers/uploadMapper.ts";



export class UploadRepositoryImpl
    implements UploadRepository {


    constructor(
        private readonly remote:
            UploadRemoteDataSource,
    ) {}



    async upload(
        file: File,

        options?: UploadOptions,

    ): Promise<UploadResult> {


         const response =
            await this.remote.upload(
                file,
                options,
            );

        return uploadMapper.toDomain(
            response,
        );
    }

}