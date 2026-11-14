import {existsSync} from "node:fs";
import {fileURLToPath, pathToFileURL} from "node:url";

const containerModuleUrl = "data:text/javascript,export const container = { orderContainer: {} };";
const explicitExtensionPattern = /\.(?:ts|tsx|js|jsx|mjs|cjs|json|node)$/i;

export async function resolve(specifier, context, nextResolve) {
    if (specifier.endsWith("/data/di/container") || specifier.endsWith("/data/di/container.ts")) {
        return {url: containerModuleUrl, shortCircuit: true};
    }

    if (specifier.startsWith(".") && !explicitExtensionPattern.test(specifier)) {
        const baseUrl = new URL(specifier, context.parentURL);
        for (const extension of [".ts", ".tsx", ".js", ".jsx", ".mjs"]) {
            const candidate = new URL(baseUrl.href + extension);
            if (existsSync(fileURLToPath(candidate))) {
                return {url: pathToFileURL(fileURLToPath(candidate)).href, shortCircuit: true};
            }
        }
    }

    return nextResolve(specifier, context);
}
