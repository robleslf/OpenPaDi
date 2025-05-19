<script>
    import { onMount } from 'svelte';
    import { initializeKeycloak } from '$lib/keycloak.js';

    onMount(async () => {
        await initializeKeycloak();
    });
</script>

<slot></slot>
