<script>
  import { initializeAuth, login, logout } from '$lib/auth';
  import { onMount } from 'svelte';

  let isAuthenticated = false;
  let user = null;

  onMount(async () => {
    const authClient = await initializeAuth();
    isAuthenticated = await authClient.isAuthenticated();
    
    if (isAuthenticated) {
      user = await authClient.getUser();
      console.log("Usuario autenticado:", user);
    }
  });

  async function handleLogin() {
    await login();
  }

  async function handleLogout() {
    await logout();
  }
</script>

<main>
  <h1>Bienvenido a OpenPaDi</h1>
  
  {#if isAuthenticated}
    <div class="user-panel">
      <p>Hola, <strong>{user?.email}</strong>!</p>
      <button on:click={handleLogout} class="btn-logout">Cerrar sesión</button>
    </div>
  {:else}
    <button on:click={handleLogin} class="btn-login">Iniciar sesión con Keycloak</button>
  {/if}
</main>

<style>
  main {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    text-align: center;
  }
  
  button {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    transition: background-color 0.3s;
  }
  
  .btn-login {
    background-color: #4299e1;
    color: white;
  }
  
  .btn-login:hover {
    background-color: #3182ce;
  }
  
  .btn-logout {
    background-color: #f56565;
    color: white;
  }
  
  .btn-logout:hover {
    background-color: #e53e3e;
  }
  
  .user-panel {
    margin-top: 2rem;
    padding: 1rem;
    background: #f7fafc;
    border-radius: 8px;
  }
</style>
