<script>
  import { onMount } from 'svelte';
  import axios from 'axios';

  let documentos = [];

  onMount(async () => {
    try {
      const response = await axios.get('http://op-api:8000/api/documentos'); // Asegúrate de que esta URL sea accesible
      documentos = response.data;
    } catch (error) {
      console.error('Error cargando documentos:', error);
    }
  });
</script>

<main>
  <h1>OpenPaDi - Repositorio de Transcripciones</h1>
  <ul>
    {#each documentos as doc}
      <li>{doc.titulo} - {doc.fecha}</li>
    {/each}
  </ul>
</main>
