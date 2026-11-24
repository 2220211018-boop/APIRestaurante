# Funciones de ayuda para el job de despliegue (Windows PowerShell 5.1 o superior).
$ErrorActionPreference = "Stop"

# Ejecuta kubectl y FALLA el paso si kubectl devuelve error (PowerShell no lo hace solo).
function k {
    & kubectl @args
    if ($LASTEXITCODE -ne 0) {
        throw "kubectl $($args -join ' ') termino con codigo $LASTEXITCODE"
    }
}

# Escribe un archivo en UTF-8 sin BOM (Windows PowerShell 5.1 escribe distinto por defecto).
$script:Utf8SinBom = New-Object System.Text.UTF8Encoding($false)
function Escribir-Archivo ($ruta, $texto) {
    [System.IO.File]::WriteAllText($ruta, $texto, $script:Utf8SinBom)
}