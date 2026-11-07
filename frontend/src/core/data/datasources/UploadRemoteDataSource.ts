import type {UploadOptions} from "../../domain/repositories/core/UploadRepository.ts";
import type {UploadFileResponseDTO} from "../dtos/upload/UploadFileResponseDTO";
import {apiClient} from "../http/http-client.ts";

export class UploadRemoteDataSource {
    async upload(file: File, options?: UploadOptions): Promise<UploadFileResponseDTO> {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("purpose", options?.purpose ?? "generic");

        const {data} = await apiClient.post<UploadFileResponseDTO>(
            "/core/upload/",
            formData,
            {
                // Override apiClient's default application/json header.
                // Axios must send FormData as multipart with a browser-generated boundary.
                headers: {"Content-Type": "multipart/form-data"},
                timeout: 120000,
                onUploadProgress(event) {
                    if (!event.total) return;
                    options?.onProgress?.(Math.round((event.loaded / event.total) * 100));
                },
            },
        );
        return data;
    }
}