# OpenPaDi 📜: Infraestructura PaaS para Humanidades Digitales

<p align="center">
  <img src="images/logo_lacre.png" alt="Logo de OpenPaDi" width="150"/>
</p>

**Open Paleography and Diplomatics** es un proyecto de infraestructura de **Plataforma como Servicio (PaaS)**, diseñado para alojar una aplicación web colaborativa para la transcripción y consulta de textos históricos. El foco de este trabajo es el diseño e implementación de una **arquitectura de sistemas y redes moderna, segura y escalable**, utilizando tecnologías de código abierto.

**Autor:** Felipe Robles López  
**Ciclo:** 2º ASIR 2024-2025

---

### ✅ Estado del Proyecto: ¿Qué Funciona Hoy?

Este proyecto ha culminado con la implementación de una **infraestructura PaaS completamente funcional** en un entorno de simulación, capaz de soportar la aplicación OpenPaDi de principio a fin.

-   **Infraestructura de Red Segura:** Redes segmentadas con **VLANs** y **Firewall (OPNsense)** controlando todo el tráfico inter-VLAN.
-   **Orquestación de Contenedores:** Clúster **Kubernetes (K3s)** desplegado, gestionando el ciclo de vida de todos los servicios de la aplicación.
-   **Servicios Desplegados y Contenerizados:**
    -   **Frontend (Svelte + Nginx)** dockerizado y servido desde el clúster. ✅
    -   **Backend API (FastAPI)** dockerizado, sirviendo la lógica de negocio. ✅
-   **Persistencia de Datos Robusta:**
    -   **Base de Datos (PostgreSQL)** en VM dedicada, operativa e integrada. ✅
    -   **Almacenamiento de Objetos (MinIO)** en VM dedicada para archivos. ✅
-   **Gestión de Identidad Centralizada:**
    -   **Keycloak** desplegado en K3s, gestionando usuarios, roles y clientes. ✅
    -   Flujo de **login/logout (SSO)** funcional desde el frontend. ✅
    -   API securizada mediante validación de **tokens JWT**. ✅
-   **Exposición Segura al Exterior:**
    -   **Traefik Ingress Controller** enrutando tráfico a los servicios correctos. ✅
    -   Conexiones cifradas con **TLS (HTTPS)** gestionadas por **Cert-Manager**. ✅

---

### 📖 Documentación del Proyecto

-   **[🔗 Repositorio en GitHub](https://github.com/robleslf/OpenPaDi)**: Acceso a todo el código fuente, manifiestos y scripts.
-   **[📄 Manual de Configuración de Red en Proxmox](./docs/Manual_de_Configuracion_de_red_en_Proxmox_VE_para_OpenPaDi.pdf)**: Guía detallada para replicar la arquitectura de red.
-   **[📄 Manual de Instalación de Servicios](./docs/Manual_de_Instalacion_Servicios_OpenPaDi.pdf)**: Guía paso a paso para desplegar todos los servicios.

---

### 🏗️ Arquitectura de la Solución (Vista de Pájaro)

OpenPaDi se ha desarrollado sobre una arquitectura moderna y escalable, utilizando **Kubernetes (K3s)** como plataforma de orquestación unificada para sus componentes principales. El frontend, el backend (API) y el servicio de autenticación se ejecutan como contenedores dentro de un clúster K3s, buscando garantizar disponibilidad, escalabilidad y una gestión eficiente. Los servicios de persistencia de datos (base de datos y almacenamiento de objetos) se han desplegado en máquinas virtuales dedicadas para este entorno de desarrollo y pruebas.

**Componentes Clave de la Arquitectura Actual:**

| Componente                               |                                                                              |
| :--------------------------------------- | :--------------------------------------------------------------------------: |
| **1. Clúster Kubernetes (K3s):** <br><ul><li>**Orquestación:** Gestiona el ciclo de vida del frontend, la API y Keycloak.</li><li>**Nodos (Entorno de Desarrollo VirtualBox):** Un nodo master (`OP-Web-1`) que también aloja el frontend y Keycloak, y un nodo worker (`OP-API-1`) para la API.</li><li>**Descubrimiento de Servicios:** DNS interno de Kubernetes para la comunicación entre pods.</li></ul> | <p align="center"><img src="images/kubernetes.png" alt="Arquitectura Kubernetes de OpenPaDi" width="70"/></p> |
| **2. Frontend (Svelte + Nginx):** <br><ul><li>Interfaz de usuario (`openpadi-frontend`) construida con Svelte y servida por Nginx contenedorizado en Docker.</li><li>Desplegada como un `Deployment` en K3s.</li><li>Accesible externamente vía Traefik Ingress en `https://openpadi.local`.</li></ul> | <p align="center"><img src="images/frontend-tri.png" alt="Interfaz de Usuario Frontend" width="140"/></p> |
| **3. Backend API (FastAPI):** <br><ul><li>Lógica de negocio (`opadi-api`), gestión de datos y comunicación con PostgreSQL y MinIO.</li><li>Desplegada como un `Deployment` en K3s (en `OP-API-1`).</li><li>Valida tokens JWT emitidos por Keycloak.</li></ul> | <p align="center"><img src="images/backend-api-arch.png" alt="Arquitectura Backend API" width="250"/></p> |
| **4. Ingress Controller (Traefik):** <br><ul><li>Gestiona el tráfico entrante al clúster K3s.</li><li>Enruta peticiones a `https://openpadi.local` (frontend y API vía path) y `https://auth.openpadi.local` (Keycloak).</li><li>Maneja la terminación TLS/SSL (actualmente con certificados autofirmados gestionados por Cert-Manager).</li></ul> | <p align="center"><img src="images/ingress-flow.png" alt="Flujo de Ingress Traefik" width="250"/></p> |
| **5. Base de Datos (PostgreSQL):** <br><ul><li>Almacena metadatos de documentos y la configuración de Keycloak.</li><li>Desplegada en una VM dedicada (`OP-db-primary`).</li></ul> | <p align="-center"><img src="images/database-arch.png" alt="Arquitectura de Base de Datos" width="250"/></p> |
| **6. Almacenamiento de Objetos (MinIO):** <br><ul><li>Almacena los archivos de documentos digitalizados.</li><li>Desplegado en una VM dedicada (`OP-Storage-1`).</li></ul> | <p align="center"><img src="images/logo_minio.png" alt="Servicios de Soporte y Almacenamiento" width="250"/></p> |
| **7. Autenticación (Keycloak):** <br><ul><li>Gestiona la identidad de los usuarios y la emisión de tokens.</li><li>Desplegado como un Pod en K3s (en `OP-Web-1`), utilizando PostgreSQL como backend.</li><li>Expuesto vía Traefik en `https://auth.openpadi.local`.</li></ul> |  <p align="center"><img src="images/logo_keycloak.png" alt="Servicios de Soporte y Almacenamiento" width="250"/></p> |

**Flujo de Tráfico Simplificado:**

1.  Un usuario accede a `https://openpadi.local`.
2.  Traefik (Ingress) recibe la petición y la dirige al frontend.
3.  El frontend Svelte se carga en el navegador. Si se requiere autenticación, redirige a `https://auth.openpadi.local`.
4.  El usuario se autentica en Keycloak. Keycloak redirige de vuelta al frontend con un token.
5.  El frontend realiza peticiones a la API (`https://openpadi.local/api/...`) incluyendo el token JWT.
6.  Traefik enruta la petición a la API. La API valida el token con Keycloak (indirectamente, usando sus claves públicas) y, si es válido, procesa la petición interactuando con PostgreSQL y MinIO.
7.  La API devuelve la respuesta al frontend, que muestra la información al usuario.

---

### 🔮 Visión de Futuro y Mejoras Propuestas

Aunque el proyecto es completamente funcional en su estado actual, la base construida permite futuras mejoras clave para un entorno de producción real:

-   **Infraestructura como Código (IaC):** Implementar herramientas como **Terraform** para automatizar el despliegue completo de la infraestructura.
-   **GitOps:** Utilizar herramientas como **Flux** para automatizar y auditar los despliegues de aplicaciones basados en commits de Git.
-   **Alta Disponibilidad (HA) Completa:** Expandir el clúster Proxmox y K3s a múltiples nodos y configurar la replicación de PostgreSQL y el modo distribuido de MinIO.
-   **Monitorización y Logging:** Implementar una pila completa con **Prometheus, Grafana y Loki** para una observabilidad total del sistema.

---

### ⚖️ Licencia

Distribuido bajo la **GNU Affero General Public License v3.0 (AGPLv3)**.
