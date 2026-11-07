export type UploadPurpose = "avatar" | "business_logo" | "generic";

export interface UploadRepository {
    upload(file: File, options?: UploadOptions): Promise<UploadResult>;
}

export interface UploadOptions {
    folder?: string;
    purpose?: UploadPurpose;
    onProgress?: (progress: number) => void;
}

export interface UploadResult {
    url: string;
    path: string;
    filename: string;
    size: number;
    contentType: string;
}