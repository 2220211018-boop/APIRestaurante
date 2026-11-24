# Guía de instalación del Runner Windows y despliegue en Kubernetes

## Requisitos previos
1. **Docker Desktop** con Kubernetes activado (`Settings -> Kubernetes -> Enable Kubernetes`).
2. Verificar en PowerShell que el clúster responde:
   ```powershell
   kubectl get nodes