# Runner Windows propio + despliegue en Kubernetes

El job de despliegue (`.github/workflows/cd.yml`) corre en TU computador Windows (runner *self-hosted*),
que tiene el clúster de Kubernetes. Así GitHub Actions puede desplegar en un clúster local.

## 1. Requisitos en el computador del runner
| Herramienta | Cómo comprobarlo |
|---|---|
| Docker Desktop con **Kubernetes activado** (Settings → Kubernetes → Enable) | `kubectl get nodes` → `Ready` |
| `kubectl` (viene con Docker Desktop) | `kubectl version --client` |
| Git | `git --version` |
| PowerShell 5.1 (ya viene en Windows) | `$PSVersionTable.PSVersion` |

## 2. Registrar el runner
1. En GitHub: repositorio → **Settings → Actions → Runners → New self-hosted runner** → **Windows / x64**.
2. Copia y ejecuta en PowerShell los comandos que muestra GitHub (descargar, descomprimir en `C:\actions-runner` y `.\config.cmd --url ... --token ...`).
   - Nombre del runner: el que quieras. Etiquetas: deja las de por defecto (`self-hosted`, `Windows`, `X64`).
3. Inícialo **en la misma sesión de usuario donde funciona `kubectl`**:
   ```powershell
   cd C:\actions-runner
   .\run.cmd
   ```
   Debe decir `Listening for Jobs` y en GitHub aparecer como **Idle** (verde).

> ⚠️ No lo instales como *servicio* de Windows con la cuenta por defecto: esa cuenta no tiene tu `~\.kube\config`
> y `kubectl` fallará. Para la demostración usa `.\run.cmd`.

## 3. Configurar los secretos del repositorio
Settings → Secrets and variables → Actions → **New repository secret**:

| Nombre | Valor |
|---|---|
| `RSA_PRIVATE_KEY` | Todo el contenido de `private_key.pem` (`Get-Content private_key.pem -Raw \| Set-Clipboard` y pegar) |
| `GHCR_PAT` *(solo si las imágenes son privadas)* | Personal Access Token (classic) con permiso `read:packages` |

Si no tienes `private_key.pem`: `pip install cryptography` y `python generar_llaves.py`.
Después de regenerar las llaves, **sube también el nuevo `public_key.pem`** al repositorio (el CD usa ese archivo).

## 4. Visibilidad de las imágenes en GHCR
Después de la primera ejecución del CI, ve a tu perfil → **Packages**. Si las 6 imágenes `apirestaurante-*` aparecen
como *Private*, haz una de estas dos cosas:
- (Fácil) En cada paquete: **Package settings → Change visibility → Public**.
- Crear el secreto `GHCR_PAT` (paso 3); el CD lo usa para que Kubernetes pueda descargar imágenes privadas.

## 5. Probar el despliegue
- Automático: al hacer merge/push a `main` y terminar el CI en verde, arranca el CD.
- Manual: **Actions → CD → Run workflow** (puedes indicar el tag/SHA de la imagen).

Comprobar desde tu máquina:
```powershell
kubectl get pods -n restaurante          # todos Running
kubectl get deployment -n restaurante -o wide   # la columna IMAGES muestra ghcr.io/...
curl http://localhost:30000/             # {"mensaje":"API Gateway del restaurante funcionando",...}
```

## 6. Problemas frecuentes
| Síntoma | Causa / solución |
|---|---|
| El job se queda en *Waiting for a runner* | El runner está apagado u *Offline*: ejecuta `.\run.cmd`. Revisa que `runs-on` coincida con sus etiquetas. |
| `kubectl no se reconoce` | `kubectl` no está en el PATH del usuario que corre el runner. Reinicia la terminal del runner. |
| `The connection to the server localhost:8080 was refused` | El runner corre con otro usuario o Kubernetes está apagado. Inícialo con tu usuario y activa Kubernetes en Docker Desktop. |
| Pods en `ImagePullBackOff` | Imágenes privadas: hazlas públicas o agrega `GHCR_PAT`. Revisa con `kubectl describe pod <pod> -n restaurante`. |
| `Falta el secreto de GitHub RSA_PRIVATE_KEY` | Crea el secreto (paso 3). |
| Prueba de humo falla | Con Minikube usa la variable `SMOKE_URL` con la URL de `minikube service gateway -n restaurante --url`. |
| Pods `CrashLoopBackOff` en el servicio de autenticación | La llave privada del secreto no corresponde a `public_key.pem`: regenera ambas y vuelve a subirlas. |

## 7. Seguridad del runner
Un runner propio ejecuta el código del repositorio en tu máquina. Por eso el CD solo se activa por el workflow `CI` en la
rama `main` (no por Pull Requests de terceros). Mantén el repositorio con colaboradores de confianza.
