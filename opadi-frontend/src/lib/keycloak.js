import Keycloak from 'keycloak-js';
import { writable } from 'svelte/store';

export const isAuthenticated = writable(false);
export const userProfile = writable(null);
export const keycloakInstance = writable(null);

let kcInstance;

const keycloakConfig = {
    url: 'https://auth.openpadi.local/',
    realm: 'openpadi',
    clientId: 'openpadi-frontend'
};

export async function initializeKeycloak() {
    if (typeof window !== 'undefined') {
        kcInstance = new Keycloak(keycloakConfig);
        keycloakInstance.set(kcInstance);

        try {
            const authenticated = await kcInstance.init({ 
                onLoad: 'check-sso',
                silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html'
            });
            
            isAuthenticated.set(authenticated);

            if (authenticated) {
                const profile = await kcInstance.loadUserProfile();
                userProfile.set(profile);
                setInterval(async () => {
                    try {
                        await kcInstance.updateToken(70);
                    } catch (err) {
                        console.error('Failed to refresh token', err);
                    }
                }, 60000);
            }
        } catch (error) {
            console.error('Failed to initialize Keycloak', error);
            isAuthenticated.set(false);
            userProfile.set(null);
        }
    }
}

export function login() {
    if (kcInstance) {
        kcInstance.login();
    }
}

export function logout() {
    if (kcInstance) {
        kcInstance.logout({ redirectUri: window.location.origin });
    }
}

export function getToken() {
    return kcInstance && kcInstance.token;
}
