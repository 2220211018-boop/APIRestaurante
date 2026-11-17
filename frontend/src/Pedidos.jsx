import { useEffect, useState } from 'react';
import { api, money } from './api';

const ESTADOS = ['PENDIENTE', 'EN_PREPARACION', 'EN_CAMINO', 'ENTREGADO', 'CANCELADO'];
const ETIQUETA = { PENDIENTE: 'Pendiente', EN_PREPARACION: 'En preparación', EN_CAMINO: 'En camino', ENTREGADO: 'Entregado', CANCELADO: 'Cancelado' };

// El servidor guarda la fecha en UTC sin zona; se la añadimos para mostrarla en hora local.
const fecha = (s) => {
  if (!s) return '';
  const d = new Date(/Z|[+-]\d\d:?\d\d$/.test(s) ? s : `${s}Z`);
  return d.toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' });
};

// admin=true: ve todos los pedidos, cambia su estado y puede eliminarlos.
// admin=false: el usuario ve solo sus pedidos (el backend ya los filtra por el JWT).
export default function Pedidos({ admin = false }) {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(null);

  const cargar = () => api.pedidos.list().then(setRows).catch((e) => setError(e.message));
  useEffect(() => { cargar(); }, []);

  async function cambiar(p, estado) {
    if (estado === p.estado) return;
    if (estado === 'CANCELADO' && !confirm(`¿Cancelar el pedido #${p.id}? El stock se devolverá al inventario.`)) return;
    setError(''); setBusy(p.id);
    try { await api.pedidos.cambiarEstado(p.id, estado); await cargar(); } catch (e) { setError(e.message); }
    setBusy(null);
  }

  async function borrar(p) {
    const aviso = p.estado === 'CANCELADO' ? '' : ' Ojo: el stock NO se devuelve; si quieres devolverlo, cancela el pedido en lugar de eliminarlo.';
    if (!confirm(`¿Eliminar el pedido #${p.id}? No se puede deshacer.${aviso}`)) return;
    setError(''); setBusy(p.id);
    try { await api.pedidos.remove(p.id); await cargar(); } catch (e) { setError(e.message); }
    setBusy(null);
  }

  return (
    <section>
      {!admin && <h1>Mis pedidos</h1>}
      {error && <p className="error" role="alert">{error}</p>}
      {!rows && !error && <p className="muted">Cargando…</p>}
      {rows?.length === 0 && <p className="muted">{admin ? 'No hay pedidos todavía.' : 'Aún no has hecho pedidos. Elige algo de la carta.'}</p>}
      {rows?.map((p) => (
        <article key={p.id} className="order">
          <header>
            <b>Pedido #{p.id}</b>
            <span className={`tag ${p.estado}`}>{ETIQUETA[p.estado] ?? p.estado}</span>
            <small>{fecha(p.creado_en)}</small>
          </header>
          <ul>
            {p.items.map((i) => (
              <li key={i.producto_id}>
                <span>{i.cantidad} × {i.nombre_producto}</span>
                <span>{money(i.subtotal)}</span>
              </li>
            ))}
          </ul>
          <p className="total"><span>Total</span><b>{money(p.total)}</b></p>
          <p className="muted">Entrega: {p.direccion_entrega}{admin && ` · Usuario ${p.usuario_id}`}</p>
          {admin && (
            <div className="row">
              <label className="inline">Estado
                <select value={p.estado} disabled={busy === p.id} onChange={(e) => cambiar(p, e.target.value)}>
                  {ESTADOS.map((e) => <option key={e} value={e}>{ETIQUETA[e]}</option>)}
                </select>
              </label>
              <button disabled={busy === p.id} onClick={() => borrar(p)}>Eliminar</button>
            </div>
          )}
        </article>
      ))}
    </section>
  );
}
