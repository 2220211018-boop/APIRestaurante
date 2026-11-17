# Frontend – Restaurante y Cafetería

React + Vite. Consume el gateway (`http://localhost:8000`) sin modificar el backend.

## Cómo correrlo
1. Levanta el backend: `docker compose up --build` (en la raíz de APIRestaurante).
2. En esta carpeta: `npm install` y `npm run dev` → http://localhost:5173
3. Si el gateway está en otra URL: `GATEWAY_URL=http://otra:8000 npm run dev`

El gateway no tiene CORS, por eso Vite reenvía `/api/*` al gateway (ver `vite.config.js`).

## Qué incluye
- Carta pública (agrupada por categoría) y carrito.
- Login / registro con JWT. Al pedir, se crea un **pedido real** (`/api/pedidos/`): el servidor calcula el total con los precios reales y descuenta el inventario (si no hay stock responde 409 y el front muestra el mensaje). Luego se crean el pago y el domicilio enlazados con `PED-<id>`.
- **Mis pedidos** (usuario): historial de sus pedidos con ítems, total y estado.
- Panel de administración (solo `ROLE_ADMIN`): CRUD de productos y clientes; **Pedidos** (ver todos, cambiar estado, cancelar → devuelve stock, eliminar); **Inventario** (registrar/editar stock y mínimo, alerta de stock bajo); lista de pagos y domicilios; resumen con pendientes y stock bajo.

## Límites del backend que el front tiene que esquivar
- `/auth/registro` siempre crea `ROLE_USER`; no hay forma de crear un admin por la API.
- Los productos sin registro de inventario no se controlan: se pueden pedir sin límite.
- Eliminar un pedido no devuelve el stock; para devolverlo hay que cancelarlo.
- `nombre_repartidor` es obligatorio en domicilios: se envía "Por asignar".
- Usuarios, pagos y domicilios viven en memoria: se pierden al reiniciar los contenedores.
- Clientes devuelve `email`/`nombre` pero pide `correo`/`nombre_completo`: se adapta en `src/api.js`.

## Ver el panel de administración (desarrollo)
El backend no permite crear admins, así que para probar localmente:
1. Desde la raíz de APIRestaurante: `pip install pyjwt cryptography` y `python frontend/scripts/token_admin.py` (usa tu `private_key.pem`, dura 8 h).
2. En el front: Ingresar → "Entrar con token de administrador" → pega el token.
3. Administración → Productos → "Cargar carta de ejemplo".
Es solo para desarrollo: el grupo debe acordar cómo crear un admin real.
