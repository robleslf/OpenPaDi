<script>
    import { onMount } from 'svelte';
    import { initKeycloak } from '$lib/keycloak.js';
    onMount(async () => {
        await initKeycloak();
    });
</script>

<slot></slot>
