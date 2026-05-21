/// <reference types="svelte" />
/// <reference types="vite/client" />

interface RuntimeConfig {
    MH_HOST?: string;
    KC_URL?: string;
    KC_REALM?: string;
    KC_CLIENT_ID?: string;
    [key: string]: string | undefined;
}

declare global {
    interface Window {
        __RUNTIME_CONFIG__?: RuntimeConfig;
    }
}

export {};
