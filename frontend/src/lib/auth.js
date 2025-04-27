import { createAuth0Client } from '@auth0/auth0-spa-js';

let auth0Client = null;

export const initializeAuth = async () => {
  auth0Client = await createAuth0Client({
    domain: "localhost:9095",
    clientId: "openpadi-frontend",
    authorizationParams: {
      redirect_uri: window.location.origin,
      audience: "openpadi-backend"
    }
  });
  return auth0Client;
};

export const login = async () => {
  await auth0Client.loginWithRedirect();
};

export const logout = async () => {
  await auth0Client.logout();
};

export const getToken = async () => {
  return await auth0Client.getTokenSilently();
};
