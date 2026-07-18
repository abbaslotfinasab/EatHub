import { UploadRemoteDataSource } from "../datasources/UploadRemoteDataSource";
import {UploadRepositoryImpl} from "../repositories/UploadRepositoryImpl.ts";
import {UploadFile} from "../../domain/use-cases/core/upload/UploadFile.ts";




export const createUploadContainer = () => {


    const remote =
        new UploadRemoteDataSource();



    const repository =
        new UploadRepositoryImpl(
            remote,
        );



    return {

        uploadFileUseCase:
            new UploadFile(
                repository,
            ),

    };

};