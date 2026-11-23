#!/usr/bin/env bash
# Ejecuta las pruebas de cada microservicio (cada uno en su propio proceso).
# Uso, desde la raíz del repo:  bash scripts/probar_todo.sh
pip install -q -r requirements-dev.txt
fallo=0
for s in gateway servicio_autenticacion servicio_clientes_productos servicio_pagos_domicilios servicio_pedidos servicio_inventario; do
  echo "=== $s ==="
  pip install -q -r "$s/requirements.txt"
  if ls "$s"/tests/test_*.py >/dev/null 2>&1; then
    python -m pytest "$s/tests" -q || fallo=1
  else
    echo "(sin pruebas todavía)"
  fi
done
exit $fallo
