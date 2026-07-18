import {
    Stack,
} from "@mui/material";

import {
    useState,
} from "react";

import {
    useFormContext,
    useWatch,
} from "react-hook-form";

import {
    UploadDropzone,
} from "./UploadDropzone";

import {
    UploadPreview,
} from "./UploadPreview";

import {
    UploadProgress,
} from "./UploadProgress";

import {
    UploadError,
} from "./UploadError";
import {useUploadFile} from "../../hooks/useUploadFile.ts";
import {buildMediaUrl} from "../../utils/media.ts";




interface UploadFieldProps {

    fileName: string;

    pathName: string;

    folder?: string;

    label?: string;

    accept?: string;

    maxSize?: number;

}



export function UploadField({

    fileName,

    pathName,

    folder = "uploads",

    accept = "image/*",

    maxSize = 5 * 1024 * 1024,

}: UploadFieldProps) {


    const {
        control,
        setValue,
    } = useFormContext();



    const file = useWatch({
        control,
        name: fileName,
    });



    const path = useWatch({
        control,
        name: pathName,
    });



    const {
        mutateAsync: uploadFile,
        progress,
        reset: resetUpload,
    } = useUploadFile();




    const [error, setError] =
        useState<string>("");



    const [status, setStatus] =
        useState<
            "idle" |
            "uploading" |
            "success" |
            "error"
        >("idle");



    /*
    |--------------------------------------------------------------------------
    | Preview Handler
    |--------------------------------------------------------------------------
    */


    const preview =
    file instanceof File
        ? URL.createObjectURL(file)
        : path
            ? buildMediaUrl(path)
            : "";



    /*
    |--------------------------------------------------------------------------
    | Upload
    |--------------------------------------------------------------------------
    */


    const handleUpload = async (
        selectedFile: File,
    ) => {


        setError("");



        if (
            selectedFile.size >
            maxSize
        ) {

            setError(
                "حجم فایل بیشتر از حد مجاز است."
            );

            setStatus("error");

            return;
        }



        setValue(
            fileName,
            selectedFile,
            {
                shouldDirty: true,
            }
        );



        try {


            setStatus(
                "uploading"
            );



            const uploadedPath =
                await uploadFile({

                    file: selectedFile,

                    folder,

                });



            setValue(
                pathName,
                uploadedPath,
                {
                    shouldDirty: true,
                }
            );



            setStatus(
                "success"
            );



        }
        catch (e) {


            console.error(
                e
            );


            setError(
                "آپلود فایل ناموفق بود."
            );


            setStatus(
                "error"
            );


        }

    };





    /*
    |--------------------------------------------------------------------------
    | Remove
    |--------------------------------------------------------------------------
    */


    const removeFile = () => {


        setValue(
            fileName,
            null,
        );


        setValue(
            pathName,
            null,
        );


        setError("");

        setStatus("idle");


        resetUpload?.();

    };





    /*
    |--------------------------------------------------------------------------
    | Retry
    |--------------------------------------------------------------------------
    */


    const retry = () => {


        if (file instanceof File) {

            handleUpload(file);

        }

    };





    return (

        <Stack
            spacing={2}
        >


            {
                !preview && (

                    <UploadDropzone

                        onSelect={
                            handleUpload
                        }

                        accept={
                            accept
                        }

                        maxSize={
                            maxSize
                        }

                    />

                )
            }





            {
                preview && (

                    <UploadPreview

                        src={
                            preview
                        }

                        filename={
                            file?.name
                        }

                        onReplace={() => {

                            const input =
                                document.querySelector(
                                    `input[type=file]`
                                );

                            (
                                input as HTMLInputElement
                            )?.click();

                        }}

                        onDelete={
                            removeFile
                        }

                    />

                )

            }






            {
                status === "uploading" && (

                    <UploadProgress

                        status="uploading"

                        progress={
                            progress
                        }

                        filename={
                            file?.name
                        }

                        size={
                            file?.size
                        }

                    />

                )
            }





            {
                status === "success" && (

                    <UploadProgress

                        status="success"

                        progress={100}

                        filename={
                            file?.name
                        }

                        size={
                            file?.size
                        }

                    />

                )
            }






            {
                status === "error" && (

                    <UploadError

                        filename={
                            file?.name
                        }

                        message={
                            error
                        }

                        onRetry={
                            retry
                        }

                        onDelete={
                            removeFile
                        }

                    />

                )
            }


        </Stack>

    );

}