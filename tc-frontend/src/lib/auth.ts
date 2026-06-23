import Keycloak from "keycloak-js";
import { getContext, setContext } from "svelte";

let _keycloak: Keycloak | null = null;
let _initialized = false;
let _roles: string[] = [];
let _authResolve: ((state: AuthState) => void) | null = null;
export const authReady: Promise<AuthState> = new Promise((resolve) => {
    _authResolve = resolve;
});

export interface KeycloakConfig {
    url: string;
    realm: string;
    clientId: string;
}

export interface AuthState {
    authenticated: boolean;
    user: { sub: string; name: string } | null;
    token: string | null;
    roles: string[];
}

export function initKeycloak(config?: KeycloakConfig): Keycloak {
    if (_keycloak) return _keycloak;
    if (!config) throw new Error("Keycloak config required");

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

        if (authenticated && kc.tokenParsed) {
            const tp = kc.tokenParsed as any;
            const resourceAccess = tp.resource_access as Record<string, { roles?: string[] }> | undefined;
            const clientRoles = resourceAccess?.[config.clientId]?.roles ?? [];
            const realmRoles = (tp.realm_access as { roles?: string[] } | undefined)?.roles ?? [];
            _roles = [...new Set([...clientRoles, ...realmRoles])];
        }

        const state = getAuthState();
        _authResolve?.(state);
        return state;
    } catch (e) {
        _initialized = true;
        const state: AuthState = { authenticated: false, user: null, token: null, roles: [] };
        _authResolve?.(state);
        return state;
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
    if (!_initialized) {
        await authReady;
    }
    if (!_keycloak || !_keycloak.authenticated) return null;
    try {
        await _keycloak.updateToken(30);
        return _keycloak.token || null;
    } catch {
        return null;
    }
}

export function getAuthState(): AuthState {
    const kc = _keycloak;
    if (!kc || !kc.authenticated) {
        return { authenticated: false, user: null, token: null, roles: [] };
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
        roles: _roles,
    };
}

export function isAuthInitialized(): boolean {
    return _initialized;
}

export function isAuthenticated(): boolean {
    return _keycloak?.authenticated ?? false;
}

export function hasRole(role: string): boolean {
    return _roles.includes(role);
}

export function hasAnyRole(...roles: string[]): boolean {
    return roles.some((r) => _roles.includes(r));
}

export function getRoles(): string[] {
    return _roles;
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

export function setAuthContext(getter: () => AuthState) {
    setContext(AUTH_KEY, getter);
}

export function getAuthContext(): AuthState {
    return (getContext(AUTH_KEY) as () => AuthState)();
}
