import {useCallback} from "react";

export interface PrintReceiptOptions {
    title?: string;
    width?: number;
    height?: number;

    /**
     * Optional callback before opening print window.
     */
    beforePrint?(): void;

    /**
     * Optional callback after print dialog is triggered.
     */
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
                    node => node.outerHTML
                )
                .join("\n");


        /*
        |--------------------------------------------------------------------------
        | Print document
        |--------------------------------------------------------------------------
        */

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
        | Wait for document
        |--------------------------------------------------------------------------
        */

        const executePrint = () => {

            printWindow.focus();

            printWindow.print();

            options?.afterPrint?.();

        };


        /*
        |--------------------------------------------------------------------------
        | Wait for images
        |--------------------------------------------------------------------------
        */

        const waitForImages = async () => {

            const images =
                Array.from(
                    printWindow.document.images,
                );

            if (images.length === 0) {

                return;

            }

            await Promise.all(
                images.map(
                    image => {

                        if (image.complete) {

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
        | Execute
        |--------------------------------------------------------------------------
        */

        const run = async () => {

            await waitForImages();

            setTimeout(
                executePrint,
                200,
            );

        };


        if (
            printWindow.document.readyState ===
            "complete"
        ) {

            void run();

        } else {

            printWindow.onload = () => {

                void run();

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
    | Generic receipt
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


    const saveReceiptPdf = useCallback(() => {

        print("receipt-pdf", {
            title: "رسید سفارش",
        });

    }, [print]);


    return {

        print,

        printReceipt,

        printReceipt58,

        printReceipt80,

        saveReceiptPdf,


    };

}