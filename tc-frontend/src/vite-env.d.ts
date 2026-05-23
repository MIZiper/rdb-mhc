/// <reference types="svelte" />
/// <reference types="vite/client" />

interface RuntimeConfig {
    MH_HOST?: string;
    [key: string]: string | undefined;
}

declare global {
    interface Window {
        __RUNTIME_CONFIG__?: RuntimeConfig;
    }
}

export {};
