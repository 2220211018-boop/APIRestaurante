# Ejecuta las pruebas de cada microservicio (cada uno en su propio proceso).
# Uso, desde la raíz del repo:  .\scripts\probar_todo.ps1
pip install -q -r requirements-dev.txt
$fallo = $false
foreach ($s in "gateway","servicio_autenticacion","servicio_clientes_productos","servicio_pagos_domicilios","servicio_pedidos","servicio_inventario") {
    Write-Host "=== $s ==="
    pip install -q -r "$s/requirements.txt"
    if (Test-Path "$s/tests") {
        python -m pytest "$s/tests" -q
        if ($LASTEXITCODE -ne 0) { $fallo = $true }
    } else { Write-Host "(sin pruebas todavía)" }
}
if ($fallo) { exit 1 }
