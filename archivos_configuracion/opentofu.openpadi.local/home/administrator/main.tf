terraform {
  required_providers {
    proxmox = {
      source = "telmate/proxmox"
      version = "2.9.14"
    }
  }
}

provider "proxmox" {
  # URL de la API de Proxmox (IP de tu servidor)
  pm_api_url = "https://192.168.1.138:8006/api2/json"

  # Token ID (formato: Usuario@Realm!NombreToken)
  pm_api_token_id = "opentofu_token"  # Ejemplo real: "root@pam!opentofu-token"

  # Secret del token (el valor que compartiste)
  pm_api_token_secret = "9497656c-97db-41f2-b044-858cf6e3b856"

  # Permitir certificados no válidos (solo para pruebas)
  pm_tls_insecure = true
}

resource "proxmox_vm_qemu" "k3s-node" {
  name        = "k3s-node-01"        # Nombre de la VM en Proxmox
  target_node = "proxmox-host"       # Nombre de tu nodo Proxmox (ver en la web)
  clone       = "debian-12-template" # Plantilla a clonar (debe existir)
  cores       = 2                    # Núcleos de CPU
  memory      = 4096                 # RAM en MB (4GB)
  agent       = 1                    # Habilita el agente QEMU

  # Configuración de red
  network {
    bridge = "vmbr2"    # Bridge para la red interna (configurado en Proxmox)
    model  = "virtio"   # Controlador de red recomendado
  }

  # Configuración del disco
  disk {
    storage = "local-lvm"  # Almacenamiento en Proxmox
    type    = "scsi"       # Tipo de disco
    size    = "20G"        # Tamaño del disco
    format  = "raw"        # Formato del disco
  }
}
