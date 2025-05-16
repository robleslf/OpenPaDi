# OpenPaDi 📜

<p align="center">
  <img src="images/logo_lacre.png" alt="Logo de OpenPaDi" width="150"/>
</p>

**Open Paleography and Diplomatics**  
**Fecha de creación:** Abril 2025

---

## Descripción

**OpenPaDi** es una plataforma colaborativa para la transcripción y consulta de textos históricos.  
Está dirigida a investigadores, estudiantes, paleógrafos, diplomáticos e historiadores, facilitando el acceso a fuentes escritas antiguas a través de un entorno digital abierto y seguro.

---

## Funcionalidades

- Repositorio de documentos digitalizados.
- Transcripción colaborativa y validación de calidad.
- Espacios de discusión y formación especializada.
- Búsqueda avanzada por fecha, lugar y palabras clave.
- Seguridad, privacidad y gestión de usuarios.

---

## Principios de Funcionamiento y Arquitectura

OpenPaDi se está diseñando sobre una arquitectura moderna y escalable, utilizando **Kubernetes (k3s)** como plataforma de orquestación unificada para todos sus componentes. Esto significa que tanto el frontend como el backend (API) se ejecutan como contenedores dentro de un clúster de Kubernetes, garantizando alta disponibilidad, escalabilidad y una gestión eficiente de los recursos.

**Componentes Clave de la Arquitectura:**

1.  **Clúster Kubernetes (k3s):**
    *   **Orquestación:** Gestiona el ciclo de vida de las aplicaciones (frontend y API), incluyendo despliegues, escalado automático y auto-reparación.
    *   **Nodos:** El clúster consta de nodos maestros (control-plane) y nodos trabajadores (workers) que ejecutan las cargas de trabajo. En nuestro entorno de desarrollo inicial, utilizamos máquinas virtuales (ej. `OP-Web-1` como master, `OP-API-1` como worker).
    *   **Descubrimiento de Servicios:** Facilita la comunicación interna entre el frontend y la API mediante el DNS de Kubernetes.

2.  **Frontend (opadi-frontend):**
    *   La interfaz de usuario con la que interactúan los paleógrafos e investigadores.
    *   Se empaqueta como una imagen Docker y se despliega como un `Deployment` en Kubernetes.
    *   Accesible externamente a través de un `Ingress Controller` (como Traefik).

3.  **Backend API (opadi-api):**
    *   Proporciona la lógica de negocio, gestión de datos y comunicación con la base de datos.
    *   También se empaqueta como imagen Docker y se despliega como un `Deployment` en Kubernetes.
    *   Se comunica de forma segura y eficiente con el frontend dentro del clúster.

4.  **Ingress Controller (Traefik):**
    *   Gestiona el tráfico entrante al clúster, dirigiendo las peticiones de los usuarios al servicio de frontend correspondiente (ej. `https://openpadi.local`).
    *   Maneja la terminación TLS/SSL para conexiones seguras.

5.  **Base de Datos (PostgreSQL/MariaDB):**
    *   Almacena los documentos, transcripciones, metadatos y datos de usuario.
    *   Inicialmente, se plantea como un servicio externo al clúster Kubernetes para simplificar la gestión, pero con la posibilidad de integrarla en Kubernetes mediante `StatefulSets` en el futuro.

6.  **Servicios de Soporte:**
    *   **Monitorización (Prometheus, Grafana):** Para observar el rendimiento y estado del sistema.
    *   **Logging (Loki):** Para la agregación y consulta centralizada de logs.
    *   **Backups:** Para la protección de datos críticos.
    *   **Firewall/Router (pfSense/VyOS):** Para la seguridad perimetral y enrutamiento de red entre VLANs (DMZ, Kubernetes, Base de Datos, etc.).

**Flujo de Tráfico Simplificado:**

1.  Un usuario accede a la URL de OpenPaDi (ej. `https://openpadi.local`).
2.  La petición llega al Ingress Controller (Traefik) dentro del clúster Kubernetes.
3.  Traefik enruta la petición al servicio del frontend.
4.  El frontend (ejecutándose en el navegador del usuario) realiza peticiones a la API (ej. `openpadi.local/api/...` o directamente al servicio interno de la API).
5.  La API procesa la petición, interactúa con la base de datos si es necesario, y devuelve la respuesta al frontend.
6.  El frontend muestra la información al usuario.

Esta arquitectura proporciona una base robusta para el desarrollo y la operación de OpenPaDi, permitiendo un crecimiento flexible y un mantenimiento simplificado.

---

## Estado

🚧 Proyecto en fase inicial de diseño y desarrollo. Actualmente definiendo la arquitectura de la infraestructura y comenzando con los primeros componentes de la aplicación.

---

## Licencia

Distribuido bajo la **GNU Affero General Public License v3.0 (AGPLv3)**.

---

# 🌟 ¡Contribuye a democratizar la paleografía digital!
