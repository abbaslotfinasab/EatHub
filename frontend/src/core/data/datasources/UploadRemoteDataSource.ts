import type { UploadOptions } from "../../domain/repositories/core/UploadRepository.ts";
import type { UploadFileResponseDTO } from "../dtos/upload/UploadFileResponseDTO";
import {apiClient} from "../http/http-client.ts";


export class UploadRemoteDataSource {


    async upload(
        file: File,

        options?: UploadOptions,

    ): Promise<UploadFileResponseDTO> {


        const formData =
            new FormData();


        formData.append(
            "file",
            file,
        );


        if (options?.folder) {

            formData.append(
                "folder",
                options.folder,
            );

        }


        const {data} =
            await apiClient.post<UploadFileResponseDTO>(
                "/core/upload/",
                formData,
                {
                    headers:{
                        "Content-Type":
                            "multipart/form-data",
                    },


                    onUploadProgress(event) {

                        if (!event.total) {
                            return;
                        }


                        const progress =
                            Math.round(
                                (
                                    event.loaded /
                                    event.total
                                ) * 100
                            );


                        options?.onProgress?.(
                            progress,
                        );

                    },

                },
            );


        return data;

    }

}