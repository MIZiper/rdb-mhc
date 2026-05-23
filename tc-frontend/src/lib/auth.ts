import Keycloak from "keycloak-js";
import { getContext, setContext } from "svelte";

let _keycloak: Keycloak | null = null;
let _initialized = false;

export interface KeycloakConfig {
    url: string;
    realm: string;
    clientId: string;
}

export interface AuthState {
    authenticated: boolean;
    user: { sub: string; name: string } | null;
    token: string | null;
}

export function initKeycloak(config: KeycloakConfig): Keycloak {
    if (_keycloak) return _keycloak;

    _keycloak = new Keycloak(config);

    _keycloak.onTokenExpired = () => {
        _keycloak!.updateToken(30).catch(() => {
            _keycloak!.logout();
        });
    };

    return _keycloak;
}

export async function checkAuth(config: KeycloakConfig): Promise<AuthState> {
    const kc = initKeycloak(config);

    if (_initialized) {
        return getAuthState();
    }

    try {
        const authenticated = await kc.init({
            onLoad: "check-sso",
            silentCheckSsoRedirectUri:
                window.location.origin + "/silent-check-sso.html",
            checkLoginIframe: false,
        });
        _initialized = true;
        return getAuthState();
    } catch (e) {
        _initialized = true;
        return { authenticated: false, user: null, token: null };
    }
}

export async function login(config: KeycloakConfig): Promise<void> {
    const kc = initKeycloak(config);
    await kc.login({ redirectUri: window.location.origin + "/" });
}

export async function logout(config: KeycloakConfig): Promise<void> {
    const kc = initKeycloak(config);
    await kc.logout({ redirectUri: window.location.href });
}

export async function getToken(): Promise<string | null> {
    const kc = initKeycloak();
    if (!kc.authenticated) return null;
    try {
        await kc.updateToken(30);
        return kc.token || null;
    } catch {
        return null;
    }
}

export function getAuthState(): AuthState {
    const kc = _keycloak;
    if (!kc || !kc.authenticated) {
        return { authenticated: false, user: null, token: null };
    }
    return {
        authenticated: true,
        user: {
            sub: kc.subject || kc.tokenParsed?.sub || "",
            name:
                kc.tokenParsed?.name ||
                kc.tokenParsed?.preferred_username ||
                kc.subject ||
                "",
        },
        token: kc.token || null,
    };
}

export function isAuthenticated(): boolean {
    return _keycloak?.authenticated ?? false;
}

export function authFetch(
    input: RequestInfo | URL,
    init?: RequestInit,
): Promise<Response> {
    return getToken().then((token) => {
        const headers = new Headers(init?.headers);
        if (token) {
            headers.set("Authorization", `Bearer ${token}`);
        }
        return fetch(input, { ...init, headers });
    });
}

const AUTH_KEY = Symbol("auth");

export function setAuthContext(state: AuthState) {
    setContext(AUTH_KEY, state);
}

export function getAuthContext(): AuthState {
    return getContext(AUTH_KEY) as AuthState;
}
