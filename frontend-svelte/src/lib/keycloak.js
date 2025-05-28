import Keycloak from 'keycloak-js';

let keycloakInstance = null;

const keycloakConfig = {
    url: 'https://auth.openpadi.local/',
    realm: 'openpadi',
    clientId: 'openpadi-frontend'
};

export function getKeycloak() {
    if (!keycloakInstance) {
        keycloakInstance = new Keycloak(keycloakConfig);
    }
    return keycloakInstance;
}

export async function initKeycloak() {
    const keycloak = getKeycloak();
    try {
        const authenticated = await keycloak.init({ 
            onLoad: 'check-sso',
            silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html'
        });
        
        if (authenticated) {
            setInterval(() => {
                keycloak.updateToken(30).then(refreshed => {
                    if (refreshed) {
                        // Token refrescado
                    } else {
                        // Token no refrescado
                    }
                }).catch(() => {
                    keycloak.logout(); 
                });
            }, 60000); 
        }
        return authenticated;
    } catch (error) {
        console.error("Failed to initialize Keycloak adapter:", error);
        return false;
    }
}
