import Keycloak from 'keycloak-js';

const keycloakConfig = {
    url: "http://localhost:9095",
    realm: "openpadi",
    clientId: "openpadi-frontend"
};

const keycloak = new Keycloak(keycloakConfig);

export const initializeAuth = async () => {
    try {
        const authenticated = await keycloak.init({
            onLoad: "check-sso",
            pkceMethod: "S256",
            silentCheckSsoRedirectUri: window.location.origin + "/silent-check-sso.html"
        });
        return authenticated;
    } catch (error) {
        console.error("Error inicializando Keycloak:", error);
        return false;
    }
};

export const login = () => keycloak.login();
export const logout = () => keycloak.logout({ redirectUri: window.location.origin });
export const getToken = () => keycloak.token;
export const getUser = () => keycloak.tokenParsed;
