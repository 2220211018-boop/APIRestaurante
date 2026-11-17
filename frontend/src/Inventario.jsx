import { useEffect, useState } from 'react';
import { api } from './api';

// Panel de inventario (solo admin). El inventario se identifica por producto_id.
export default function Inventario() {
  const [inv, setInv] = useState(null);
  const [prods, setProds] = useState([]);
  const [form, setForm] = useState(null); // null = cerrado; { producto_id, stock, stock_minimo, editando }
  const [error, setError] = useState('');

  async function cargar() {
    try {
      const [i, p] = await Promise.all([api.inventario.list(), api.productos.list()]);
      setInv(i); setProds(p);
    } catch (e) { setError(e.message); }
  }
  useEffect(() => { cargar(); }, []);

  const nombre = (id) => prods.find((p) => p.id === id)?.nombre ?? `Producto ${id}`;
  const sinInventario = prods.filter((p) => !inv?.some((i) => i.producto_id === p.id));
  const bajos = (inv || []).filter((i) => i.bajo_minimo);

  const nuevo = () => setForm({ producto_id: sinInventario[0].id, stock: 0, stock_minimo: 5, editando: false });

  async function guardar(e) {
    e.preventDefault();
    setError('');
    const cuerpo = { stock: parseInt(form.stock, 10), stock_minimo: parseInt(form.stock_minimo, 10) };
    try {
      if (form.editando) await api.inventario.update(form.producto_id, cuerpo);
      else await api.inventario.create({ producto_id: Number(form.producto_id), ...cuerpo });
      setForm(null);
      cargar();
    } catch (err) { setError(err.message); }
  }

  async function borrar(i) {
    if (!confirm(`¿Dejar de controlar el inventario de "${nombre(i.producto_id)}"? Se podrá pedir sin límite de stock.`)) return;
    try { await api.inventario.remove(i.producto_id); cargar(); } catch (err) { setError(err.message); }
  }

  const estado = (i) => (i.agotado ? 'Agotado' : i.bajo_minimo ? 'Stock bajo' : 'OK');

  return (
    <section>
      {error && <p className="error" role="alert">{error}</p>}
      {bajos.length > 0 && (
        <p className="aviso" role="status">
          ⚠️ Stock bajo o agotado: {bajos.map((i) => `${nombre(i.producto_id)} (${i.stock})`).join(', ')}
        </p>
      )}
      {!form && <button className="primary" disabled={sinInventario.length === 0} onClick={nuevo}>Registrar stock</button>}
      {!form && inv && prods.length > 0 && sinInventario.length === 0 && <small className="seed">Todos los productos ya tienen inventario.</small>}
      {!form && prods.length === 0 && inv && <small className="seed">Primero crea productos en la pestaña Productos.</small>}
      {form && (
        <form className="panel" onSubmit={guardar}>
          <h2>{form.editando ? `Editar stock de ${nombre(form.producto_id)}` : 'Registrar stock'}</h2>
          {!form.editando && (
            <label>Producto
              <select value={form.producto_id} onChange={(e) => setForm({ ...form, producto_id: e.target.value })}>
                {sinInventario.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
              </select>
            </label>
          )}
          <label>Stock actual<input required type="number" min="0" step="1" value={form.stock} onChange={(e) => setForm({ ...form, stock: e.target.value })} /></label>
          <label>Stock mínimo (alerta)<input required type="number" min="0" step="1" value={form.stock_minimo} onChange={(e) => setForm({ ...form, stock_minimo: e.target.value })} /></label>
          <div className="row"><button className="primary">Guardar</button><button type="button" onClick={() => setForm(null)}>Cancelar</button></div>
        </form>
      )}
      {!inv && !error && <p className="muted">Cargando…</p>}
      {inv?.length === 0 && <p className="muted">Ningún producto controla inventario todavía. Los productos sin registro se pueden pedir sin límite.</p>}
      {inv?.length > 0 && (
        <div className="scroll">
          <table>
            <thead><tr><th>Producto</th><th>Stock</th><th>Mínimo</th><th>Estado</th><th /></tr></thead>
            <tbody>
              {inv.map((i) => (
                <tr key={i.producto_id}>
                  <td>{nombre(i.producto_id)}</td>
                  <td>{i.stock}</td>
                  <td>{i.stock_minimo}</td>
                  <td><span className={`tag ${i.agotado ? 'CANCELADO' : i.bajo_minimo ? 'PENDIENTE' : 'ENTREGADO'}`}>{estado(i)}</span></td>
                  <td className="acts">
                    <button onClick={() => setForm({ producto_id: i.producto_id, stock: i.stock, stock_minimo: i.stock_minimo, editando: true })}>Editar</button>
                    <button onClick={() => borrar(i)}>Eliminar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
