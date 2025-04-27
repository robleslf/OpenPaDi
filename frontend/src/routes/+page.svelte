<script>
  import { initializeAuth, login, logout } from '$lib/auth';
  import { onMount } from 'svelte';
  
  let authLoading = true;
  let isAuthenticated = false;
  let user = null;

  onMount(async () => {
    try {
      const authClient = await initializeAuth();
      isAuthenticated = await authClient.isAuthenticated();
      
      if (isAuthenticated) {
        user = await authClient.getUser();
        console.log("Usuario autenticado:", user);
      }
    } catch (error) {
      console.error("Error de autenticación:", error);
    } finally {
      authLoading = false;
    }
  });

  async function handleLogin() {
    await login();
  }

  async function handleLogout() {
    await logout();
  }
</script>

{#if authLoading}
  <div class="loading">Verificando autenticación...</div>
{:else if isAuthenticated}
  <main>
    <h1>Bienvenido a OpenPaDi</h1>
    <div class="user-panel">
      <p>👋 Hola, <strong>{user?.email}</strong></p>
      <button on:click={handleLogout} class="btn-logout">Cerrar sesión</button>
    </div>
  </main>
{:else}
  <main>
    <h1>OpenPaDi - Transcripciones Colaborativas</h1>
    <button on:click={handleLogin} class="btn-login">
      🔑 Iniciar sesión con Keycloak
    </button>
  </main>
{/if}

<style>
  main {
    max-width: 800px;
    margin: 2rem auto;
    padding: 2rem;
    text-align: center;
    background: #f8fafc;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }

  .loading {
    text-align: center;
    padding: 2rem;
    color: #4a5568;
  }

  button {
    padding: 0.8rem 1.5rem;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1.1rem;
    transition: transform 0.2s, box-shadow 0.2s;
  }

  .btn-login {
    background: #4299e1;
    color: white;
    font-weight: bold;
  }

  .btn-login:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(66, 153, 225, 0.4);
  }

  .btn-logout {
    background: #f56565;
    color: white;
    margin-top: 1rem;
  }

  .user-panel {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    margin-top: 2rem;
  }
</style>
