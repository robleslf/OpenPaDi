<script>
    import { onMount } from 'svelte';
    import axios from 'axios';
    import { getKeycloak, initKeycloak } from '$lib/keycloak.js';

    let documentos = [];
    let formTitulo = '';
    let formFecha = '';
    let formContenido = '';
    let formArchivo = null;

    let errorMessage = '';
    let successMessage = '';
    let isLoading = true;
    
    let keycloak = null;
    let isAuthenticated = false;
    let userInfo = null;

    onMount(async () => {
        keycloak = getKeycloak();
        try {
            isAuthenticated = await initKeycloak();
            if (isAuthenticated) {
                try {
                    userInfo = await keycloak.loadUserProfile();
                } catch (e) {
                    userInfo = { username: 'usuario (perfil no cargado)'};
                }
                await fetchDocumentos();
            }
        } catch (error) {
            isAuthenticated = false;
        } finally {
            isLoading = false;
        }
    });

    async function fetchDocumentos() {
        isLoading = true;
        errorMessage = '';
        try {
            const config = {};
            if (isAuthenticated && keycloak && keycloak.token) {
                config.headers = { 'Authorization': `Bearer ${keycloak.token}` };
            }
            const response = await axios.get('/api/documentos', config);
            documentos = response.data;
        } catch (error) {
            errorMessage = 'Error al cargar la lista de documentos.';
            documentos = [];
        } finally {
            isLoading = false;
        }
    }

    function handleFileChange(event) {
        if (event.target.files && event.target.files.length > 0) {
            formArchivo = event.target.files[0];
        } else {
            formArchivo = null;
        }
    }

    async function handleSubmit() {
        if (!isAuthenticated || !keycloak || !keycloak.token) {
            errorMessage = "Debes iniciar sesión para crear un documento.";
            return;
        }

        errorMessage = '';
        successMessage = '';
        if (!formTitulo.trim()) {
            errorMessage = 'El título es obligatorio.';
            return;
        }

        const formData = new FormData();
        formData.append('titulo', formTitulo);
        if (formFecha) formData.append('fecha', formFecha);
        if (formContenido) formData.append('contenido', formContenido);
        if (formArchivo) formData.append('archivo', formArchivo);

        try {
            const config = {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    'Authorization': `Bearer ${keycloak.token}`
                }
            };
            const response = await axios.post('/api/documentos', formData, config);
            successMessage = `Documento "${response.data.titulo}" creado con éxito (ID: ${response.data.id}).`;
            await fetchDocumentos();
            prepareNewDocumentForm();
        } catch (error) {
            if (error.response && error.response.data && error.response.data.detail) {
                errorMessage = `Error al guardar el documento: ${error.response.data.detail}`;
            } else if (error.response && error.response.status === 401) {
                errorMessage = 'Error de autenticación al crear. Tu sesión puede haber expirado.';
            }
            else {
                errorMessage = 'Error desconocido al guardar el documento.';
            }
        }
    }

    function prepareNewDocumentForm() {
        formTitulo = '';
        formFecha = '';
        formContenido = '';
        formArchivo = null;
        const fileInput = document.getElementById('archivo');
        if (fileInput) fileInput.value = '';
        successMessage = '';
        errorMessage = '';
    }

    function login() {
        if (keycloak) keycloak.login();
    }

    function logout() {
        if (keycloak) keycloak.logout({ redirectUri: window.location.origin });
    }
    
    async function handleDownloadArchivo(docId, docTitulo) {
        errorMessage = '';
        successMessage = '';
        if (!isAuthenticated || !keycloak || !keycloak.token) {
            errorMessage = "Debes iniciar sesión para descargar archivos.";
            return;
        }
        try {
            const config = { headers: { 'Authorization': `Bearer ${keycloak.token}` } };
            const response = await axios.get(`/api/documentos/${docId}/archivo`, config);
            if (response.data && response.data.url_descarga) {
                window.open(response.data.url_descarga, '_blank');
                successMessage = `Preparando descarga para "${docTitulo}"...`;
            } else {
                errorMessage = "No se pudo obtener la URL de descarga.";
            }
        } catch (error) {
            if (error.response && error.response.data && error.response.data.detail) {
                errorMessage = `Error al obtener archivo: ${error.response.data.detail}`;
            } else {
                errorMessage = 'Error desconocido al obtener el archivo.';
            }
        }
    }
</script>

<main>
    <div class="logo-header">
        <img src="/logo-openpadi.png" alt="Logo OpenPaDi" class="logo-openpadi"/>
    </div>
    <h1>OpenPaDi - Repositorio de Transcripciones</h1>

    {#if isLoading}
        <div class="loader-container">
            <div class="spinner"></div>
            {#if !isAuthenticated}
                <p>Inicializando autenticación...</p>
            {:else}
                <p>Cargando datos...</p>
            {/if}
        </div>
    {:else if !isAuthenticated}
        <div class="loader-container">
            <p>Por favor, inicia sesión para continuar.</p>
            <button on:click={login}>Iniciar Sesión con Keycloak</button>
        </div>
    {/if}

    {#if isAuthenticated}
        <p>Bienvenido, {userInfo?.username || 'usuario'}!</p>
        <button on:click={logout}>Cerrar Sesión</button>

        <form on:submit|preventDefault={handleSubmit}>
            <h2>Crear Nuevo Documento</h2>
            <div>
                <label for="titulo-form">Título:</label>
                <input type="text" id="titulo-form" bind:value={formTitulo} required />
            </div>
            <div>
                <label for="fecha-form">Fecha (YYYY-MM-DD):</label>
                <input type="date" id="fecha-form" bind:value={formFecha} />
            </div>
            <div>
                <label for="contenido-form">Contenido:</label>
                <textarea id="contenido-form" bind:value={formContenido}></textarea>
            </div>
            <div>
                <label for="archivo">Archivo (PDF, Imagen, etc.):</label>
                <input type="file" id="archivo" on:change={handleFileChange} />
            </div>
            <button type="submit">Crear Documento</button>
        </form>
        
        {#if errorMessage}
            <p style="color: red;">{errorMessage}</p>
        {/if}
        {#if successMessage}
            <p style="color: green;">{successMessage}</p>
        {/if}

        <h2>Documentos Existentes</h2>
        {#if isLoading && isAuthenticated}
            <div class="loader-container">
                 <div class="spinner"></div>
                 <p>Cargando documentos...</p>
            </div>
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
                    </li>
                {/each}
            </ul>
        {/if}
    {/if}
</main>

<style>
    main {
        font-family: sans-serif;
        padding: 1em;
        max-width: 800px;
        margin: 0 auto;
    }
    .logo-header {
        text-align: center;
        margin-bottom: 1em;
    }
    .logo-openpadi {
        max-width: 150px;
        height: auto;
    }
    .loader-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 200px;
    }
    .spinner {
        border: 4px solid rgba(0, 0, 0, 0.1);
        width: 36px;
        height: 36px;
        border-radius: 50%;
        border-left-color: #007bff;
        animation: spin 1s ease infinite;
        margin-bottom: 1em;
    }
    @keyframes spin {
        0% {
            transform: rotate(0deg);
        }
        100% {
            transform: rotate(360deg);
        }
    }
    form {
        border: 1px solid #ccc;
        padding: 1em;
        margin-bottom: 2em;
        border-radius: 4px;
    }
    form div {
        margin-bottom: 1em;
    }
    label {
        display: block;
        margin-bottom: 0.25em;
    }
    input[type="text"],
    input[type="date"],
    textarea,
    input[type="file"] {
        width: 100%;
        padding: 0.5em;
        box-sizing: border-box;
        border: 1px solid #ccc;
        border-radius: 4px;
    }
    textarea {
        min-height: 80px;
    }
    button {
        padding: 0.7em 1.5em;
        border: none;
        background-color: #007bff;
        color: white;
        border-radius: 4px;
        cursor: pointer;
        margin-right: 0.5em;
        margin-top: 0.5em;
    }
    button:hover {
        opacity: 0.9;
    }
    ul {
        list-style: none;
        padding: 0;
    }
    li {
        border: 1px solid #eee;
        padding: 1em;
        margin-bottom: 0.5em;
        border-radius: 4px;
    }
</style>
