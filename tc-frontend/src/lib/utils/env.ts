/** Read a value from the runtime config injected at container start. */
export const getConfig = (key: string): string | undefined => {
    if (window.__RUNTIME_CONFIG__) {
        return window.__RUNTIME_CONFIG__[key];
    }
    console.warn(`Runtime config for "${key}" not found.`);
    return undefined;
};
