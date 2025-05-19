<script>
    import { onMount } from 'svelte';
    import axios from 'axios';
    import { isAuthenticated, userProfile, login, logout, getToken } from '$lib/keycloak.js';

    let documentos = [];
    let currentId = null;
    let formTitulo = '';
    let formFecha = '';
    let formContenido = '';
    let formArchivo = null;
    
    let errorMessage = '';
    let successMessage = '';
    let isLoading = true;

    async function fetchDocumentos() {
        isLoading = true;
        errorMessage = '';
        try {
            const config = {};
            if ($isAuthenticated && getToken()) {
                config.headers = { 'Authorization': `Bearer ${getToken()}` };
            }
            const response = await axios.get('/api/documentos', config); 
            documentos = response.data;
        } catch (error) {
            console.error('Error cargando documentos:', error);
            if (error.response && error.response.status === 401) {
                errorMessage = 'No autorizado para ver documentos. Por favor, inicie sesión.';
            } else {
                errorMessage = 'Error al cargar la lista de documentos.';
            }
            documentos = [];
        } finally {
            isLoading = false;
        }
    }

    $: if (typeof window !== 'undefined') {
         if ($isAuthenticated === true || $isAuthenticated === false) {
            fetchDocumentos();
         }
    }
    onMount(fetchDocumentos);

    function prepareNewDocumentForm() {
        currentId = null;
        formTitulo = '';
        formFecha = '';
        formContenido = '';
        formArchivo = null; 
        const fileInput = document.getElementById('archivo');
        if (fileInput) fileInput.value = '';
        successMessage = '';
        errorMessage = '';
    }

    function prepareEditForm(doc) {
        currentId = doc.id;
        formTitulo = doc.titulo;
        formFecha = doc.fecha ? doc.fecha.toString().split('T')[0] : '';
        formContenido = doc.contenido || '';
        formArchivo = null;
        const fileInput = document.getElementById('archivo');
        if (fileInput) fileInput.value = '';
        successMessage = '';
        errorMessage = '';
    }

    function handleFileChange(event) {
        if (event.target.files.length > 0) {
            formArchivo = event.target.files[0];
        } else {
            formArchivo = null;
        }
    }

    async function handleSubmit() {
        errorMessage = '';
        successMessage = '';

        if (!$isAuthenticated) {
            errorMessage = 'Debe iniciar sesión para realizar esta acción.';
            login();
            return;
        }

        if (!formTitulo.trim()) {
            errorMessage = 'El título es obligatorio.';
            return;
        }

        const formData = new FormData();
        formData.append('titulo', formTitulo);
        if (formFecha) formData.append('fecha', formFecha);
        if (formContenido) formData.append('contenido', formContenido);
        if (formArchivo && !currentId) formData.append('archivo', formArchivo);

        try {
            const token = getToken();
            if (!token) {
                errorMessage = 'Token no disponible. Por favor, inicie sesión de nuevo.';
                login();
                return;
            }

            const config = {
                headers: {
                    'Authorization': `Bearer ${token}`,
                }
            };
            
            let response;
            if (currentId) {
                const putData = { titulo: formTitulo, fecha: formFecha || null, contenido: formContenido || null };
                response = await axios.put(`/api/documentos/${currentId}`, putData, {
                     headers: { 'Authorization': `Bearer ${token}` }
                });
                successMessage = `Documento "${response.data.titulo}" actualizado con éxito (ID: ${response.data.id}).`;
            } else {
                response = await axios.post('/api/documentos', formData, config);
                successMessage = `Documento "${response.data.titulo}" creado con éxito (ID: ${response.data.id}).`;
            }
            await fetchDocumentos(); 
            prepareNewDocumentForm();
        } catch (error) {
            console.error('Error guardando documento:', error);
            if (error.response && error.response.data && error.response.data.detail) {
                errorMessage = `Error al guardar el documento: ${error.response.data.detail}`;
            } else {
                errorMessage = 'Error desconocido al guardar el documento.';
            }
        }
    }

    async function handleDelete(id, titulo) {
        if (!$isAuthenticated) {
            errorMessage = 'Debe iniciar sesión para eliminar.';
            login();
            return;
        }
        if (!confirm(`¿Estás seguro de que quieres eliminar el documento "${titulo}" (ID: ${id})?`)) {
            return;
        }
        errorMessage = '';
        successMessage = '';
        try {
            const token = getToken();
            if (!token) throw new Error("Token no disponible");
            await axios.delete(`/api/documentos/${id}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            successMessage = `Documento "${titulo}" (ID: ${id}) eliminado con éxito.`;
            await fetchDocumentos();
            if (currentId === id) {
                prepareNewDocumentForm();
            }
        } catch (error) {
            console.error('Error eliminando documento:', error);
            if (error.response && error.response.data && error.response.data.detail) {
                errorMessage = `Error al eliminar el documento: ${error.response.data.detail}`;
            } else {
                errorMessage = 'Error desconocido al eliminar el documento.';
            }
        }
    }

    async function handleDownloadArchivo(docId, docTitulo) {
        if (!$isAuthenticated && false) { 
            errorMessage = 'Debe iniciar sesión para descargar archivos.';
            login();
            return;
        }
        errorMessage = '';
        successMessage = '';
        try {
            const config = {};
            if ($isAuthenticated && getToken()) {
                 config.headers = { 'Authorization': `Bearer ${getToken()}` };
            }
            const response = await axios.get(`/api/documentos/${docId}/archivo`, config);
            if (response.data && response.data.url_descarga) {
                window.open(response.data.url_descarga, '_blank');
                successMessage = `Preparando descarga para "${docTitulo}"...`;
            } else {
                errorMessage = "No se pudo obtener la URL de descarga.";
            }
        } catch (error) {
            console.error('Error obteniendo URL de descarga:', error);
            if (error.response && error.response.data && error.response.data.detail) {
                errorMessage = `Error al obtener archivo: ${error.response.data.detail}`;
            } else {
                errorMessage = 'Error desconocido al obtener el archivo.';
            }
        }
    }
</script>

<main>
    <h1>OpenPaDi - Repositorio de Transcripciones</h1>

    <div>
        {#if $isAuthenticated}
            <p>
                Bienvenido, {$userProfile?.username || 'usuario'}! 
                ({$userProfile?.email || 'Sin email'})
                <button on:click={logout}>Cerrar Sesión</button>
            </p>
        {:else}
            <p>No has iniciado sesión.</p>
            <button on:click={login}>Iniciar Sesión con Keycloak</button>
        {/if}
    </div>

    {#if errorMessage}
        <p style="color: red;">{errorMessage}</p>
    {/if}
    {#if successMessage}
        <p style="color: green;">{successMessage}</p>
    {/if}

    {#if $isAuthenticated}
        <form on:submit|preventDefault={handleSubmit}>
            <h2>{currentId ? 'Editar Documento (ID: ' + currentId + ')' : 'Crear Nuevo Documento'}</h2>
            <div>
                <label for="titulo">Título:</label>
                <input type="text" id="titulo" bind:value={formTitulo} required />
            </div>
            <div>
                <label for="fecha">Fecha (YYYY-MM-DD):</label>
                <input type="date" id="fecha" bind:value={formFecha} />
            </div>
            <div>
                <label for="contenido">Contenido:</label>
                <textarea id="contenido" bind:value={formContenido}></textarea>
            </div>
            {#if !currentId}
                <div>
                    <label for="archivo">Archivo (PDF, Imagen, etc.):</label>
                    <input type="file" id="archivo" on:change={handleFileChange} />
                </div>
            {/if}
            <button type="submit">{currentId ? 'Guardar Cambios' : 'Crear Documento'}</button>
            {#if currentId}
                <button type="button" on:click={prepareNewDocumentForm}>Cancelar Edición (Crear Nuevo)</button>
            {/if}
        </form>
    {/if}

    <h2>Documentos Existentes</h2>
    {#if isLoading}
        <p>Cargando documentos...</p>
    {:else if documentos.length === 0 && !errorMessage}
        <p>No hay documentos para mostrar.</p>
    {:else}
        <ul>
            {#each documentos as doc (doc.id)}
                <li>
                    <strong>{doc.titulo}</strong> (ID: {doc.id})<br />
                    Fecha: {doc.fecha || 'N/A'}<br />
                    Contenido: {doc.contenido || 'N/A'}<br />
                    {#if doc.minio_object_key}
                        <button on:click={() => handleDownloadArchivo(doc.id, doc.titulo)}>Ver/Descargar Archivo</button>
                    {/if}
                    {#if $isAuthenticated}
                        <button on:click={() => prepareEditForm(doc)}>Editar</button>
                        <button on:click={() => handleDelete(doc.id, doc.titulo)}>Eliminar</button>
                    {/if}
                </li>
            {/each}
        </ul>
    {/if}
</main>

<style>
    main { font-family: sans-serif; padding: 1em; max-width: 800px; margin: 0 auto; }
    form { border: 1px solid #ccc; padding: 1em; margin-bottom: 2em; border-radius: 4px; }
    form div { margin-bottom: 1em; }
    label { display: block; margin-bottom: 0.25em; }
    input[type="text"], input[type="date"], textarea, input[type="file"] {
        width: 100%; padding: 0.5em; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px;
    }
    textarea { min-height: 80px; }
    button {
        padding: 0.7em 1.5em; border: none; background-color: #007bff; color: white;
        border-radius: 4px; cursor: pointer; margin-right: 0.5em; margin-top: 0.5em;
    }
    button[type="button"] { background-color: #6c757d; }
    button:hover { opacity: 0.9; }
    ul { list-style: none; padding: 0; }
    li { border: 1px solid #eee; padding: 1em; margin-bottom: 0.5em; border-radius: 4px; }
</style>
