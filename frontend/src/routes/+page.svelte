<script>
  import { initializeAuth, login, logout, getUser } from '$lib/auth';
  import { onMount } from 'svelte';

  let isAuthenticated = false;
  let user = null;

  onMount(async () => {
    isAuthenticated = await initializeAuth();
    if (isAuthenticated) {
      user = getUser();
      console.log("Usuario autenticado:", user);
    }
  });
</script>

<main>
  <h1>Bienvenido a OpenPaDi</h1>
  {#if isAuthenticated}
    <div class="user-panel">
      <p>Hola, <strong>{user?.email}</strong>!</p>
      <button on:click={logout} class="btn-logout">Cerrar sesión</button>
    </div>
  {:else}
    <button on:click={login} class="btn-login">Iniciar sesión con Keycloak</button>
  {/if}
</main>
