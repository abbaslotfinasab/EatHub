import {useCallback} from "react";


/* ================================================================
   Types
================================================================ */


export interface PrintReceiptOptions {

    /**
     * Browser print window title.
     */
    title?: string;

    /**
     * Popup window width.
     */
    width?: number;

    /**
     * Popup window height.
     */
    height?: number;

    /**
     * Additional CSS injected into print document.
     */
    css?: string;

    /**
     * Called immediately before opening print window.
     */
    beforePrint?(): void;

    /**
     * Called after printing finishes.
     */
    afterPrint?(): void;

    /**
     * Automatically close print window after print.
     *
     * Default: true
     */
    closeAfterPrint?: boolean;

    /**
     * Delay before calling window.print().
     *
     * Useful for fonts/images/rendering.
     *
     * Default: 100ms
     */
    printDelay?: number;

}


/* ================================================================
   Constants
================================================================ */


const DEFAULT_POPUP_WIDTH = 900;

const DEFAULT_POPUP_HEIGHT = 1000;

const DEFAULT_PRINT_DELAY = 100;


/* ================================================================
   Hook
================================================================ */


export function usePrintReceipt() {


    /* ============================================================
       Copy Styles
    ============================================================ */


    const collectStyles =
        useCallback((): string => {

            const nodes =
                Array.from(
                    document.querySelectorAll(
                        'style, link[rel="stylesheet"]',
                    ),
                );


            return nodes
                .map((node) => {

                    /*
                     * Clone the node instead of using outerHTML
                     * directly so we don't mutate the original DOM.
                     */

                    return node.cloneNode(true) as HTMLElement;

                })
                .map((node) => {

                    /*
                     * For <link> elements, make sure relative URLs
                     * resolve against the current application URL.
                     */

                    if (
                        node instanceof HTMLLinkElement
                    ) {

                        const href =
                            node.getAttribute("href");


                        if (href) {

                            try {

                                node.setAttribute(
                                    "href",
                                    new URL(
                                        href,
                                        document.baseURI,
                                    ).href,
                                );

                            } catch {

                                /*
                                 * Ignore invalid URLs.
                                 */

                            }

                        }

                    }


                    return node.outerHTML;

                })
                .join("\n");

        }, []);


    /* ============================================================
       Wait for Stylesheets
    ============================================================ */


    const waitForStylesheets =
        useCallback(
            async (
                printDocument: Document,
            ): Promise<void> => {

                const links =
                    Array.from(
                        printDocument.querySelectorAll(
                            'link[rel="stylesheet"]',
                        ),
                    );


                await Promise.all(

                    links.map(
                        (element) => {

                            const link =
                                element as HTMLLinkElement;


                            /*
                             * Already loaded.
                             */

                            if (
                                link.sheet
                            ) {

                                return Promise.resolve();

                            }


                            return new Promise<void>(
                                (resolve) => {

                                    let settled =
                                        false;


                                    const finish =
                                        () => {

                                            if (
                                                settled
                                            ) {

                                                return;

                                            }


                                            settled =
                                                true;


                                            resolve();

                                        };


                                    link.addEventListener(
                                        "load",
                                        finish,
                                        {
                                            once: true,
                                        },
                                    );


                                    link.addEventListener(
                                        "error",
                                        finish,
                                        {
                                            once: true,
                                        },
                                    );


                                    /*
                                     * Safety timeout.
                                     *
                                     * We don't want a broken external
                                     * stylesheet to block printing forever.
                                     */

                                    window.setTimeout(
                                        finish,
                                        5000,
                                    );

                                },
                            );

                        },
                    ),

                );

            },
            [],
        );


    /* ============================================================
       Wait for Fonts
    ============================================================ */


    const waitForFonts =
        useCallback(
            async (
                printDocument: Document,
            ): Promise<void> => {

                if (
                    !("fonts" in printDocument)
                ) {

                    return;

                }


                try {

                    /*
                     * Wait for the browser's font loading process.
                     */

                    await printDocument.fonts.ready;


                    /*
                     * Explicitly ask browser to load the main
                     * application font if it exists.
                     */

                    try {

                        await printDocument.fonts.load(
                            '10px "Vazirmatn"',
                        );

                    } catch {

                        /*
                         * Font may not exist.
                         * Browser fallback is acceptable.
                         */

                    }

                } catch {

                    /*
                     * Don't block printing because of fonts.
                     */

                }

            },
            [],
        );


    /* ============================================================
       Wait for Images
    ============================================================ */


    const waitForImages =
        useCallback(
            async (
                printDocument: Document,
            ): Promise<void> => {

                const images =
                    Array.from(
                        printDocument.images,
                    );


                if (
                    images.length === 0
                ) {

                    return;

                }


                await Promise.all(

                    images.map(
                        (image) => {

                            /*
                             * Already loaded.
                             */

                            if (
                                image.complete &&
                                image.naturalWidth > 0
                            ) {

                                return Promise.resolve();

                            }


                            return new Promise<void>(
                                (resolve) => {

                                    let settled =
                                        false;


                                    const finish =
                                        () => {

                                            if (
                                                settled
                                            ) {

                                                return;

                                            }


                                            settled =
                                                true;


                                            resolve();

                                        };


                                    image.addEventListener(
                                        "load",
                                        finish,
                                        {
                                            once: true,
                                        },
                                    );


                                    image.addEventListener(
                                        "error",
                                        finish,
                                        {
                                            once: true,
                                        },
                                    );


                                    /*
                                     * Safety timeout.
                                     */

                                    window.setTimeout(
                                        finish,
                                        5000,
                                    );

                                },
                            );

                        },
                    ),

                );

            },
            [],
        );


    /* ============================================================
       Wait for Rendering
    ============================================================ */


    const waitForRender =
        useCallback(
            async (): Promise<void> => {

                /*
                 * Give browser one animation frame to perform
                 * layout and paint.
                 */

                await new Promise<void>(
                    (resolve) => {

                        requestAnimationFrame(
                            () => {

                                requestAnimationFrame(
                                    () => {

                                        resolve();

                                    },
                                );

                            },
                        );

                    },
                );

            },
            [],
        );


    /* ============================================================
       Main Print Function
    ============================================================ */


    const print =
        useCallback(
            (
                elementId: string,
                options?: PrintReceiptOptions,
            ) => {

                const element =
                    document.getElementById(
                        elementId,
                    );


                if (!element) {

                    console.error(
                        `[PrintReceipt] Element #${elementId} not found.`,
                    );

                    return;

                }


                /*
                 * Execute callback before opening popup.
                 */

                options?.beforePrint?.();


                const width =
                    options?.width ??
                    DEFAULT_POPUP_WIDTH;


                const height =
                    options?.height ??
                    DEFAULT_POPUP_HEIGHT;


                /*
                 * IMPORTANT:
                 *
                 * window.open must happen synchronously inside
                 * the user interaction event.
                 *
                 * Otherwise Chrome may block the popup.
                 */

                const printWindow =
                    window.open(
                        "",
                        "_blank",
                        [
                            `width=${width}`,
                            `height=${height}`,
                            "left=0",
                            "top=0",
                            "noopener=no",
                            "resizable=yes",
                            "scrollbars=yes",
                        ].join(","),
                    );


                if (!printWindow) {

                    console.error(
                        "[PrintReceipt] Could not open print window. Popup may be blocked.",
                    );

                    options?.afterPrint?.();

                    return;

                }


                /*
                 * ------------------------------------------------
                 * Prepare HTML
                 * ------------------------------------------------
                 */


                const styles =
                    collectStyles();


                /*
                 * The receipt element itself.
                 *
                 * We clone it so we don't mutate the live UI.
                 */

                const receipt =
                    element.cloneNode(
                        true,
                    ) as HTMLElement;


                /*
                 * Remove any accidental action / interactive
                 * elements from the cloned document.
                 *
                 * This is mostly useful for generic print calls.
                 */

                receipt
                    .querySelectorAll(
                        "button, input, select, textarea",
                    )
                    .forEach(
                        (node) => {

                            node.remove();

                        },
                    );


                /*
                 * Convert relative image URLs to absolute URLs.
                 */

                receipt
                    .querySelectorAll("img")
                    .forEach(
                        (image) => {

                            const src =
                                image.getAttribute(
                                    "src",
                                );


                            if (
                                !src
                            ) {

                                return;

                            }


                            try {

                                image.setAttribute(
                                    "src",
                                    new URL(
                                        src,
                                        document.baseURI,
                                    ).href,
                                );

                            } catch {

                                /*
                                 * Keep original src.
                                 */

                            }

                        },
                    );


                /*
                 * Convert relative source URLs in inline styles.
                 *
                 * Useful for background-image / url(...)
                 */

                receipt
                    .querySelectorAll<HTMLElement>(
                        "[style]",
                    )
                    .forEach(
                        (node) => {

                            const style =
                                node.getAttribute(
                                    "style",
                                );


                            if (
                                !style ||
                                !style.includes("url(")
                            ) {

                                return;

                            }


                            /*
                             * Browser will generally resolve these
                             * against <base>, so no aggressive parsing
                             * is needed here.
                             */

                        },
                    );


                /*
                 * ------------------------------------------------
                 * Write Document
                 * ------------------------------------------------
                 */

                const documentTitle =
                    escapeHtml(
                        options?.title ??
                        "رسید سفارش",
                    );


                const baseHref =
                    escapeHtml(
                        document.baseURI,
                    );


                printWindow.document.open();


                printWindow.document.write(
                    `<!DOCTYPE html>
<html lang="fa" dir="rtl">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <base href="${baseHref}">

    <title>${documentTitle}</title>

    ${styles}

    <style>

        /* ========================================================
           Print Reset
        ======================================================== */

        html,
        body {

            margin: 0 !important;

            padding: 0 !important;

            width: 100%;

            min-height: 100%;

            background: #ffffff;

            color: #000000;

            direction: rtl;

        }


        *,
        *::before,
        *::after {

            box-sizing: border-box;

        }


        body {

            font-family:
                "Vazirmatn",
                Tahoma,
                Arial,
                sans-serif;

            -webkit-print-color-adjust: exact !important;

            print-color-adjust: exact !important;

        }


        img {

            max-width: 100%;

        }


        @media print {

            html,
            body {

                margin: 0 !important;

                padding: 0 !important;

                background: #ffffff !important;

            }


            body {

                width: 100%;

            }


            @page {

                margin: 0;

            }

        }


        /* ========================================================
           Custom CSS
        ======================================================== */

        ${options?.css ?? ""}

    </style>

</head>


<body>

    ${receipt.outerHTML}

</body>

</html>`,
                );


                printWindow.document.close();


                /*
                 * ------------------------------------------------
                 * Print Lifecycle
                 * ------------------------------------------------
                 */


                let printed =
                    false;


                const finish =
                    () => {

                        if (
                            options?.closeAfterPrint !== false
                        ) {

                            try {

                                printWindow.close();

                            } catch {

                                /*
                                 * Ignore close errors.
                                 */

                            }

                        }


                        options?.afterPrint?.();

                    };


                const executePrint =
                    async () => {

                        /*
                         * Wait until linked stylesheets are ready.
                         */

                        await waitForStylesheets(
                            printWindow.document,
                        );


                        /*
                         * Wait for fonts.
                         */

                        await waitForFonts(
                            printWindow.document,
                        );


                        /*
                         * Wait for images.
                         */

                        await waitForImages(
                            printWindow.document,
                        );


                        /*
                         * Wait for browser layout.
                         */

                        await waitForRender();


                        /*
                         * Small configurable delay.
                         */

                        const delay =
                            options?.printDelay ??
                            DEFAULT_PRINT_DELAY;


                        if (
                            delay > 0
                        ) {

                            await new Promise<void>(
                                (resolve) => {

                                    window.setTimeout(
                                        resolve,
                                        delay,
                                    );

                                },
                            );

                        }


                        /*
                         * Prevent duplicate print() calls.
                         */

                        if (
                            printed
                        ) {

                            return;

                        }


                        printed =
                            true;


                        /*
                         * Focus print window before opening
                         * browser print dialog.
                         */

                        printWindow.focus();


                        printWindow.print();

                    };


                /*
                 * Browser fires afterprint when print dialog
                 * finishes / closes.
                 */

                printWindow.addEventListener(
                    "afterprint",
                    finish,
                    {
                        once: true,
                    },
                );


                /*
                 * Start loading/printing.
                 */

                void executePrint();

            },
            [
                collectStyles,
                waitForStylesheets,
                waitForFonts,
                waitForImages,
                waitForRender,
            ],
        );


    /* ============================================================
       Thermal 58mm
    ============================================================ */


    const printReceipt58 =
        useCallback(
            () => {

                print(
                    "receipt-58",
                    {
                        title: "رسید سفارش",
                        width: 500,
                        height: 900,
                    },
                );

            },
            [print],
        );


    /* ============================================================
       Thermal 80mm
    ============================================================ */


    const printReceipt80 =
        useCallback(
            () => {

                print(
                    "receipt-80",
                    {
                        title: "رسید سفارش",
                        width: 700,
                        height: 1000,
                    },
                );

            },
            [print],
        );


    /* ============================================================
       Generic Receipt Print
    ============================================================ */


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


    /* ============================================================
       Save PDF
    ============================================================ */


    const saveReceiptPdf =
        useCallback(
            () => {

                print(
                    "receipt-pdf",
                    {
                        title: "رسید سفارش",
                        width: 900,
                        height: 1100,
                    },
                );

            },
            [print],
        );


    /* ============================================================
       Return
    ============================================================ */


    return {

        print,

        printReceipt,

        printReceipt58,

        printReceipt80,

        saveReceiptPdf,

    };

}


/* ================================================================
   Helpers
================================================================ */


/**
 * Escape HTML values that are inserted into document.write().
 */
function escapeHtml(
    value: string,
): string {

    return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}