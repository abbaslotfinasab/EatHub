const containerModuleUrl = "data:text/javascript,export const container = { orderContainer: {} };";

export async function resolve(specifier, context, nextResolve) {
    if (specifier.endsWith("/data/di/container.ts")) {
        return {url: containerModuleUrl, shortCircuit: true};
    }
    return nextResolve(specifier, context);
}
