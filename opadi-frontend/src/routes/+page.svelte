<script>
  import { onMount } from 'svelte';
  import axios from 'axios';

  let documentos = [];

  onMount(async () => {
    try {
	const response = await axios.get('/api/documentos');
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
