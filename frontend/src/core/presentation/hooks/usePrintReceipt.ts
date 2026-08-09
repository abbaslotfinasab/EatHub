import {useCallback} from "react";

export interface PrintReceiptOptions {
    title?: string;

    width?: number;

    height?: number;

    beforePrint?(): void;

    afterPrint?(): void;
}


export function usePrintReceipt() {

    const print = useCallback((
        elementId: string,
        options?: PrintReceiptOptions,
    ) => {

        const element =
            document.getElementById(elementId);


        if (!element) {

            console.error(
                `[PrintReceipt] Element #${elementId} not found.`,
            );

            return;

        }


        options?.beforePrint?.();


        const printWindow =
            window.open(
                "",
                "_blank",
                `width=${options?.width ?? 900},height=${options?.height ?? 1000}`,
            );


        if (!printWindow) {

            console.error(
                "[PrintReceipt] Could not open print window.",
            );

            return;

        }


        /*
        |--------------------------------------------------------------------------
        | Copy application styles
        |--------------------------------------------------------------------------
        */

        const styles =
            Array.from(
                document.querySelectorAll(
                    'style, link[rel="stylesheet"]',
                ),
            )
                .map(
                    node =>
                        node.outerHTML,
                )
                .join("\n");


        /*
        |--------------------------------------------------------------------------
        | Print Document
        |--------------------------------------------------------------------------
        */

        printWindow.document.open();


        printWindow.document.write(`

            <!DOCTYPE html>

            <html
                lang="fa"
                dir="rtl"
            >

            <head>

                <meta charset="UTF-8"/>

                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1.0"
                />

                <base
                    href="${document.baseURI}"
                />

                <title>
                    ${options?.title ?? "رسید سفارش"}
                </title>


                ${styles}


                <style>

                    html,
                    body {

                        margin: 0;

                        padding: 0;

                        background: #ffffff;

                        direction: rtl;

                    }


                    *,
                    *::before,
                    *::after {

                        box-sizing: border-box;

                        -webkit-print-color-adjust: exact !important;

                        print-color-adjust: exact !important;

                    }


                    body {

                        font-family:
                            "Vazirmatn",
                            "Tahoma",
                            "Arial",
                            sans-serif;

                    }


                    @page {

                        margin: 0;

                        size: auto;

                    }


                    @media print {

                        html,
                        body {

                            margin: 0 !important;

                            padding: 0 !important;

                        }

                    }

                </style>

            </head>


            <body>

                ${element.outerHTML}

            </body>

            </html>

        `);


        printWindow.document.close();


        /*
        |--------------------------------------------------------------------------
        | Wait for Stylesheets
        |--------------------------------------------------------------------------
        */

        const waitForStylesheets =
            async () => {

                const stylesheets =
                    Array.from(
                        printWindow.document.querySelectorAll(
                            'link[rel="stylesheet"]',
                        ),
                    );


                await Promise.all(

                    stylesheets.map(
                        stylesheet => {

                            const link =
                                stylesheet as HTMLLinkElement;


                            if (link.sheet) {

                                return Promise.resolve();

                            }


                            return new Promise<void>(
                                resolve => {

                                    link.onload =
                                        () => resolve();


                                    link.onerror =
                                        () => resolve();

                                },
                            );

                        },
                    ),

                );

            };


        /*
        |--------------------------------------------------------------------------
        | Wait for Fonts
        |--------------------------------------------------------------------------
        */

        const waitForFonts =
            async () => {

                if (
                    "fonts" in
                    printWindow.document
                ) {

                    await
                        printWindow.document
                            .fonts
                            .ready;

                }

            };


        /*
        |--------------------------------------------------------------------------
        | Wait for Images
        |--------------------------------------------------------------------------
        */

        const waitForImages =
            async () => {

                const images =
                    Array.from(
                        printWindow.document.images,
                    );


                if (
                    images.length === 0
                ) {

                    return;

                }


                await Promise.all(

                    images.map(
                        image => {

                            if (
                                image.complete
                            ) {

                                return Promise.resolve();

                            }


                            return new Promise<void>(
                                resolve => {

                                    image.onload =
                                        () => resolve();


                                    image.onerror =
                                        () => resolve();

                                },
                            );

                        },
                    ),

                );

            };


        /*
        |--------------------------------------------------------------------------
        | Execute Print
        |--------------------------------------------------------------------------
        */

        const executePrint =
            async () => {

                await waitForStylesheets();

                await waitForFonts();

                await waitForImages();


                setTimeout(() => {

                    printWindow.focus();

                    printWindow.print();

                }, 300);

            };


        /*
        |--------------------------------------------------------------------------
        | Close Window
        |--------------------------------------------------------------------------
        */

        printWindow.onafterprint =
            () => {

                printWindow.close();

                options?.afterPrint?.();

            };


        /*
        |--------------------------------------------------------------------------
        | Start
        |--------------------------------------------------------------------------
        */

        if (
            printWindow.document.readyState ===
            "complete"
        ) {

            void executePrint();

        } else {

            printWindow.onload =
                () => {

                    void executePrint();

                };

        }

    }, []);


    /*
    |--------------------------------------------------------------------------
    | Receipt 58mm
    |--------------------------------------------------------------------------
    */

    const printReceipt58 =
        useCallback(() => {

            print(
                "receipt-58",
                {
                    title: "رسید سفارش",
                    width: 500,
                    height: 800,
                },
            );

        }, [print]);


    /*
    |--------------------------------------------------------------------------
    | Receipt 80mm
    |--------------------------------------------------------------------------
    */

    const printReceipt80 =
        useCallback(() => {

            print(
                "receipt-80",
                {
                    title: "رسید سفارش",
                    width: 700,
                    height: 900,
                },
            );

        }, [print]);


    /*
    |--------------------------------------------------------------------------
    | Generic Print
    |--------------------------------------------------------------------------
    */

    const printReceipt =
        useCallback(
            (
                elementId: string,
                title = "رسید سفارش",
            ) => {

                print(
                    elementId,
                    {
                        title,
                    },
                );

            },
            [print],
        );


    /*
    |--------------------------------------------------------------------------
    | Save PDF
    |--------------------------------------------------------------------------
    |
    | Browser print dialog:
    |
    | Print → Save as PDF
    |
    */

    const saveReceiptPdf =
        useCallback(() => {

            print(
                "receipt-pdf",
                {
                    title: "رسید سفارش",
                },
            );

        }, [print]);


    return {

        print,

        printReceipt,

        printReceipt58,

        printReceipt80,

        saveReceiptPdf,

    };

}