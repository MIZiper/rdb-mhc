export const getConfig = (key: string) => {
    if (window.__RUNTIME_CONFIG__) {
        return window.__RUNTIME_CONFIG__[key];
    }
    console.warn(`Runtime config for "${key}" not found.`)
}