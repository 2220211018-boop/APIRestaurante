# Despliega todo en Kubernetes (PowerShell). Ejecutar desde la RAÍZ del proyecto:  .\k8s\desplegar.ps1
$ErrorActionPreference = "Stop"

if (-not (Test-Path private_key.pem)) { python generar_llaves.py }

Write-Host "1) Construyendo imagenes Docker..."
docker build -t apirestaurante/autenticacion:1.0 ./servicio_autenticacion
docker build -t apirestaurante/clientes-productos:1.0 -f servicio_clientes_productos/Dockerfile .
docker build -t apirestaurante/pagos-domicilios:1.0 -f servicio_pagos_domicilios/Dockerfile .
docker build -t apirestaurante/pedidos:1.0 -f servicio_pedidos/Dockerfile .
docker build -t apirestaurante/inventario:1.0 -f servicio_inventario/Dockerfile .
docker build -t apirestaurante/gateway:1.0 ./gateway

# Solo si usas Minikube (con Docker Desktop Kubernetes NO hace falta):
# minikube image load apirestaurante/autenticacion:1.0 apirestaurante/clientes-productos:1.0 apirestaurante/pagos-domicilios:1.0 apirestaurante/pedidos:1.0 apirestaurante/inventario:1.0 apirestaurante/gateway:1.0

Write-Host "2) Namespace y secretos (llaves RSA)..."
kubectl apply -f k8s/00-namespace.yaml
kubectl delete secret rsa-private-key rsa-public-key -n restaurante --ignore-not-found
kubectl create secret generic rsa-private-key --from-file=private_key.pem -n restaurante
kubectl create secret generic rsa-public-key  --from-file=public_key.pem  -n restaurante

Write-Host "3) Aplicando manifiestos..."
kubectl apply -f k8s/

Write-Host "4) Esperando pods..."
kubectl rollout status deployment/postgres -n restaurante --timeout=180s
kubectl rollout status deployment/servicio-autenticacion -n restaurante --timeout=180s
kubectl rollout status deployment/servicio-clientes-productos -n restaurante --timeout=180s
kubectl rollout status deployment/servicio-pagos-domicilios -n restaurante --timeout=180s
kubectl rollout status deployment/servicio-pedidos -n restaurante --timeout=180s
kubectl rollout status deployment/servicio-inventario -n restaurante --timeout=180s
kubectl rollout status deployment/gateway -n restaurante --timeout=180s
kubectl get pods,svc -n restaurante
Write-Host "Listo: http://localhost:30000  (Swagger auth: kubectl port-forward svc/servicio-autenticacion 4004:8000 -n restaurante)"
