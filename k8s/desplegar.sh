#!/usr/bin/env bash
# Despliega todo en Kubernetes (Linux/Mac/Git Bash). Ejecutar desde la RAIZ: bash k8s/desplegar.sh
set -e
[ -f private_key.pem ] || python generar_llaves.py

docker build -t apirestaurante/autenticacion:1.0 ./servicio_autenticacion
docker build -t apirestaurante/clientes-productos:1.0 -f servicio_clientes_productos/Dockerfile .
docker build -t apirestaurante/pagos-domicilios:1.0 -f servicio_pagos_domicilios/Dockerfile .
docker build -t apirestaurante/pedidos:1.0 -f servicio_pedidos/Dockerfile .
docker build -t apirestaurante/inventario:1.0 -f servicio_inventario/Dockerfile .
docker build -t apirestaurante/gateway:1.0 ./gateway
# Solo Minikube: minikube image load apirestaurante/autenticacion:1.0 apirestaurante/clientes-productos:1.0 apirestaurante/pagos-domicilios:1.0 apirestaurante/pedidos:1.0 apirestaurante/inventario:1.0 apirestaurante/gateway:1.0

kubectl apply -f k8s/00-namespace.yaml
kubectl delete secret rsa-private-key rsa-public-key -n restaurante --ignore-not-found
kubectl create secret generic rsa-private-key --from-file=private_key.pem -n restaurante
kubectl create secret generic rsa-public-key  --from-file=public_key.pem  -n restaurante
kubectl apply -f k8s/

for d in postgres servicio-autenticacion servicio-clientes-productos servicio-pagos-domicilios servicio-pedidos servicio-inventario gateway; do
  kubectl rollout status deployment/$d -n restaurante --timeout=180s
done
kubectl get pods,svc -n restaurante
echo "Listo: http://localhost:30000"
