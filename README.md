# API Restaurante y Cafetería — Proyecto 03 (Web, API y Microservicios)

Aplicación web de microservicios (FastAPI + PostgreSQL + React) con API REST (GET, POST, PUT, DELETE),
seguridad **JWT firmado con RSA (RS256)** y **OAuth 2.0**, contenedores **Docker** y despliegue en **Kubernetes**.

## Arquitectura
| Componente | Descripción | Puerto |
|---|---|---|
| gateway | API Gateway: único punto de entrada `/api/<servicio>/...` | 8000 |
| servicio_autenticacion | Registro, login, OAuth2 `/auth/token`, emite JWT con la **llave privada RSA** | 4004 |
| servicio_clientes_productos | CRUD de clientes y menú (PostgreSQL). Valida JWT con la **llave pública** | 8001 |
| servicio_pagos_domicilios | Pagos y domicilios. Valida JWT con la llave pública | 8002 |
| servicio_inventario | Stock por producto (PostgreSQL). Descuenta al crear pedidos y repone al cancelarlos | 8004 |
| servicio_pedidos | Pedidos con sus ítems (PostgreSQL). Consulta precios a clientes_productos y valida JWT | 8003 |
| db (PostgreSQL 15) | Persistencia relacional | 5432 |
| frontend | React + Vite | 5173 |

Cada microservicio tiene su propio `Dockerfile`.

## Seguridad
- Contraseñas con bcrypt.
- JWT RS256: el servicio de autenticación firma con `private_key.pem`; los demás solo verifican con `public_key.pem`.
- OAuth 2.0 (flujo Password): `POST /auth/token` (botón *Authorize* de Swagger en `/docs`).
- Roles: `ROLE_ADMIN` (CRUD de productos/clientes) y `ROLE_USER`. El correo definido en `ADMIN_EMAIL` recibe `ROLE_ADMIN` al registrarse.
- `private_key.pem` NO se sube a GitHub (está en `.gitignore`): se genera con `python generar_llaves.py`.

## Ejecutar con Docker Compose
```bash
pip install cryptography
python generar_llaves.py
docker compose up --build
```
Gateway: http://localhost:8000 · Swagger auth: http://localhost:4004/docs

## Desplegar en Kubernetes
Requisitos: Docker Desktop con Kubernetes activado (o Minikube) y `kubectl`.
```powershell
.\k8s\desplegar.ps1        # Windows
bash k8s/desplegar.sh      # Linux / Mac / Git Bash
```
Gateway: http://localhost:30000 (Minikube: `minikube service gateway -n restaurante --url`).
Swagger de autenticación: `kubectl port-forward svc/servicio-autenticacion 4004:8000 -n restaurante`.

Eliminar todo: `kubectl delete namespace restaurante`.

## Frontend
Ver `frontend/README.md`. Con Kubernetes: `GATEWAY_URL=http://localhost:30000 npm run dev`.

## Pruebas rápidas
00. Inventario (admin): `POST /api/inventario/` con `{"producto_id":1,"stock":50,"stock_minimo":5}`; `GET /api/inventario/alertas` lista stock bajo.
0. Pedidos: `POST /api/pedidos/` con `{"direccion_entrega":"...","items":[{"producto_id":1,"cantidad":2}]}`.
1. `POST /api/auth/registro` con `admin@restaurante.com` → rol `ROLE_ADMIN`.
2. `POST /api/auth/login` → `access_token`.
3. `POST /api/productos/` con `Authorization: Bearer <token>`.
4. Colección Postman en `postman/`.

## Equipo
(Agregar nombres y usuarios de GitHub de cada integrante)

## Integración continua y despliegue (CI/CD)

El proyecto utiliza **GitHub Actions** para automatizar la validación del código y la construcción de las imágenes Docker. El flujo está definido en `.github/workflows/ci.yml`.

### ¿Cuándo se ejecuta?

El flujo se ejecuta cuando:

- Se realiza un `push` a la rama `main`.
- Se crea o actualiza un `pull request` dirigido a `main`.
- Se inicia manualmente desde GitHub Actions.

### Etapas del flujo

1. **Pruebas automatizadas:** ejecuta las pruebas de los microservicios `gateway`, `servicio_autenticacion`, `servicio_clientes_productos`, `servicio_pagos_domicilios`, `servicio_pedidos` y `servicio_inventario`. Las pruebas se ejecutan en paralelo con Python 3.11 y pytest. Los resultados se guardan como artefactos XML.
2. **Compilación del frontend:** instala las dependencias con `npm ci` y compila la aplicación React con `npm run build`.
3. **Validación de Kubernetes:** ejecuta `scripts/validar_k8s.py` para revisar los manifiestos de Kubernetes.
4. **Construcción y publicación de imágenes:** cuando las etapas anteriores finalizan correctamente, construye las seis imágenes Docker y las publica en GitHub Container Registry (GHCR). Esta etapa no se ejecuta en los `pull requests`.

Las imágenes se publican con dos etiquetas: el identificador del commit y `latest`.

### Ejecutar pruebas localmente

Para ejecutar las pruebas de cada microservicio, utiliza los siguientes comandos desde la raíz del proyecto:

```powershell
py -m pytest servicio_pagos_domicilios\tests -v
py -m pytest servicio_pedidos\tests -v
py -m pytest servicio_inventario\tests -v
```

### Resultados de las pruebas

| Microservicio | Pruebas aprobadas |
|---|---:|
| Pagos y domicilios | 11 |
| Pedidos | 15 |
| Inventario | 22 |
| **Total** | **48** |

Las 48 pruebas ejecutadas finalizaron correctamente, sin fallos.