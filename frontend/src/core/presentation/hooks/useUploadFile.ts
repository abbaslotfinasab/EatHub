import {
    useMutation,
} from "@tanstack/react-query";

import {
    useState,
} from "react";
import {container} from "../../data/di/container.ts";


interface UploadFileInput {

    file: File;

    folder?: string;

}



export const useUploadFile = () => {


    const {
        uploadFileUseCase,
    } = container.uploadContainer;



    const [progress, setProgress] =
        useState(0);




    const mutation =
        useMutation({

            mutationFn: async (
                input: UploadFileInput,
            ) => {


                setProgress(0);



                return await uploadFileUseCase.execute(
                    input.file,
                    {

                        folder:
                            input.folder,


                        onProgress:
                            (value:number) => {

                                setProgress(value);

                            },

                    }
                );

            },


            onSuccess: () => {

                setProgress(100);

            },


            onError: () => {

                setProgress(0);

            },

        });





    return {

        ...mutation,


        progress,


    };

};