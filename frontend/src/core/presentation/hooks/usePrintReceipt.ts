import {useCallback} from "react";

export interface PrintReceiptOptions {
    title?: string;

    beforePrint?(): void;

    afterPrint?(): void;

    width?: number;

    height?: number;
}

export function usePrintReceipt() {

    const print = useCallback((
        elementId: string,
        options?: PrintReceiptOptions,
    ) => {

        const element = document.getElementById(elementId);

        if (!element) {
            console.error(`Element #${elementId} not found.`);
            return;
        }

        options?.beforePrint?.();

        const printWindow = window.open(
            "",
            "_blank",
            `width=${options?.width ?? 900},height=${options?.height ?? 1000}`,
        );

        if (!printWindow) {
            return;
        }

        const styles = Array.from(
            document.querySelectorAll(
                'style,link[rel="stylesheet"]',
            ),
        )
            .map(node => node.outerHTML)
            .join("");

        printWindow.document.write(`
<!DOCTYPE html>

<html lang="fa" dir="rtl">

<head>

<meta charset="UTF-8"/>

<title>${options?.title ?? "Receipt"}</title>

${styles}

<style>

html,
body{

    margin:0;
    padding:0;
    background:#fff;
    direction:rtl;

}

*{
    box-sizing:border-box;
    -webkit-print-color-adjust:exact !important;
    print-color-adjust:exact !important;
}

@page{
    margin:0;
    size:auto;
}

</style>

</head>

<body>

${element.outerHTML}

</body>

</html>
`);

        printWindow.document.close();

        printWindow.focus();

        const execute = () => {

            printWindow.print();

            printWindow.close();

            options?.afterPrint?.();

        };

        if (printWindow.document.readyState === "complete") {

            setTimeout(execute, 300);

        } else {

            printWindow.onload = () => {

                setTimeout(execute, 300);

            };

        }

    }, []);

    //------------------------------------------------------------------
    // Thermal 58
    //------------------------------------------------------------------

    const printReceipt58 = useCallback(() => {

        print("receipt-58", {
            title: "Receipt 58mm",
        });

    }, [print]);

    //------------------------------------------------------------------
    // Thermal 80
    //------------------------------------------------------------------

    const printReceipt80 = useCallback(() => {

        print("receipt-80", {
            title: "Receipt 80mm",
        });

    }, [print]);

    //------------------------------------------------------------------
    // Future
    //------------------------------------------------------------------

    const printInvoice = useCallback(() => {

        print("invoice-a4", {
            title: "Invoice",
        });

    }, [print]);


    const downloadPdf58 = useCallback(async () => {

        console.log("Coming Soon");

    }, []);

    const downloadPdf80 = useCallback(async () => {

        console.log("Coming Soon");

    }, []);

    const shareReceipt58 = useCallback(async () => {

        console.log("Coming Soon");

    }, []);

    const shareReceipt80 = useCallback(async () => {

        console.log("Coming Soon");

    }, []);


    const exportPdf = useCallback(() => {

        print("receipt-card");

    }, [print]);


    return {

        print,

        printReceipt58,
        printReceipt80,

        printInvoice,

        downloadPdf58,
        downloadPdf80,

        exportPdf,


        shareReceipt58,
        shareReceipt80,
    };

}