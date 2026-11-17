import { useEffect, useMemo, useState } from 'react';
import { api, money } from './api';

const METODOS = ['EFECTIVO', 'NEQUI', 'DAVIPLATA', 'TARJETA'];
const TINTS = ['#e3efe6', '#f7e4e4', '#fbefd5', '#e2e9f5', '#efe3f3'];
const emoji = (c, n) => {
  const s = `${c} ${n}`.toLowerCase();
  if (/postre|torta|brownie|helado|arroz con leche/.test(s)) return '🍰';
  if (/fría|frío|limonada|jugo|té /.test(s)) return '🧊';
  if (/caf|tinto|capuch|chocolate|arom|caliente/.test(s)) return '☕';
  if (/desayuno|huevo|calentado|arepa|caldo/.test(s)) return '🥐';
  if (/sancocho|bandeja|plato|pechuga|almuerzo/.test(s)) return '🍽️';
  return '🍴';
};

export default function Menu({ user, cart, setCart, goLogin, isAdmin, goAdmin, goPedidos }) {
  const [items, setItems] = useState(null);
  const [error, setError] = useState('');
  const [cat, setCat] = useState('Todas');
  const [q, setQ] = useState('');

  useEffect(() => { api.productos.list().then(setItems).catch((e) => setError(e.message)); }, []);
  const cats = useMemo(() => [...new Set((items || []).map((p) => p.categoria))], [items]);
  const visibles = (items || []).filter((p) => (cat === 'Todas' || p.categoria === cat) && `${p.nombre} ${p.descripcion}`.toLowerCase().includes(q.toLowerCase()));

  const chg = (p, d) => setCart((c) => {
    const n = (c[p.id]?.n || 0) + d;
    const { [p.id]: _, ...resto } = c;
    return n > 0 ? { ...c, [p.id]: { p, n } } : resto;
  });

  return (
    <>
      <section className="hero">
        <h1>Carta</h1>
        <p>Elige lo que se te antoje y te lo llevamos a la puerta.</p>
        <input type="search" aria-label="Buscar en la carta" placeholder="Buscar un plato o bebida" value={q} onChange={(e) => setQ(e.target.value)} />
      </section>
      <div className="split">
        <section>
          {error && <p className="error">{error}</p>}
          {!items && !error && <p className="muted">Cargando la carta…</p>}
          {items?.length === 0 && (
            <div className="panel">
              <p><b>La carta está vacía.</b></p>
              {isAdmin
                ? <><p className="muted">Carga la carta de ejemplo o crea tus productos desde Administración.</p><button className="primary" onClick={goAdmin}>Ir a Administración</button></>
                : <p className="muted">Pronto agregaremos productos. Vuelve en un rato.</p>}
            </div>
          )}
          {cats.length > 1 && (
            <div className="chips">
              {['Todas', ...cats].map((c) => (
                <button key={c} className={c === cat ? 'on' : ''} onClick={() => setCat(c)}>
                  {c} <small>{c === 'Todas' ? items.length : items.filter((p) => p.categoria === c).length}</small>
                </button>
              ))}
            </div>
          )}
          {items?.length > 0 && visibles.length === 0 && <p className="muted">Nada coincide con tu búsqueda.</p>}
          {cats.filter((c) => visibles.some((p) => p.categoria === c)).map((c) => (
            <div key={c}>
              <h2>{c}</h2>
              <div className="grid">
                {visibles.filter((p) => p.categoria === c).map((p) => (
                  <article key={p.id} className={'card' + (p.disponible ? '' : ' off')}>
                    <div className="tile" style={{ background: TINTS[cats.indexOf(c) % TINTS.length] }} aria-hidden="true">{emoji(c, p.nombre)}</div>
                    <div className="info">
                      <b>{p.nombre}</b>
                      <p>{p.descripcion}</p>
                      <div className="buy">
                        <span className="price">{money(p.precio)}</span>
                        {!p.disponible ? <em>Agotado</em> : cart[p.id] ? (
                          <span className="qty">
                            <button aria-label={`Quitar uno de ${p.nombre}`} onClick={() => chg(p, -1)}>−</button>{cart[p.id].n}
                            <button aria-label={`Agregar uno de ${p.nombre}`} onClick={() => chg(p, 1)}>+</button>
                          </span>
                        ) : <button className="add" onClick={() => chg(p, 1)}>Agregar</button>}
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          ))}
        </section>
        <Comanda user={user} cart={cart} setCart={setCart} goLogin={goLogin} goPedidos={goPedidos} isAdmin={isAdmin} goAdmin={goAdmin} />
      </div>
    </>
  );
}

function Comanda({ user, cart, setCart, goLogin, goPedidos, isAdmin, goAdmin }) {
  const lines = Object.values(cart);
  const total = lines.reduce((s, { p, n }) => s + p.precio * n, 0);
  const [dir, setDir] = useState('');
  const [metodo, setMetodo] = useState('EFECTIVO');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [hecho, setHecho] = useState(null);

  const cambiar = (id, d) => setCart((c) => {
    const n = c[id].n + d;
    const { [id]: _, ...resto } = c;
    return n > 0 ? { ...c, [id]: { ...c[id], n } } : resto;
  });

  async function pedir(e) {
    e.preventDefault();
    setError(''); setBusy(true);
    let pedido;
    try {
      // 1) Pedido real: el servidor calcula el total con los precios reales y descuenta el inventario
      //    (responde 409 si no hay stock suficiente y entonces no se crea nada).
      const r = await api.pedidos.create({
        direccion_entrega: dir,
        items: lines.map(({ p, n }) => ({ producto_id: p.id, cantidad: n })),
      });
      pedido = r.pedido;
    } catch (err) { setError(err.message); setBusy(false); return; }

    // 2) Pago y domicilio quedan enlazados al pedido por su id.
    const id_pedido = `PED-${pedido.id}`;
    let aviso = '';
    try {
      await api.pagos.create({ id_pedido, monto: pedido.total, metodo_pago: metodo, estado: metodo === 'EFECTIVO' ? 'PENDIENTE' : 'COMPLETADO' });
      await api.domicilios.create({ id_pedido, direccion_entrega: dir, nombre_repartidor: 'Por asignar', estado_envio: 'PREPARANDO' });
    } catch (err) { aviso = `Tu pedido se creó, pero no se pudo registrar el pago o el domicilio: ${err.message}`; }
    setHecho({ id: id_pedido, total: pedido.total, dir, aviso });
    setCart({});
    setBusy(false);
  }

  if (hecho) return (
    <aside className="ticket">
      <h2>Pedido recibido</h2>
      <p><b>{hecho.id}</b></p>
      <p>Total {money(hecho.total)}. Lo llevamos a {hecho.dir}.</p>
      {hecho.aviso && <p className="error" role="alert">{hecho.aviso}</p>}
      <button className="primary" onClick={isAdmin ? goAdmin : goPedidos}>{isAdmin ? 'Ver pedidos en Administración' : 'Ver mis pedidos'}</button>
      <button className="link" onClick={() => setHecho(null)}>Hacer otro pedido</button>
    </aside>
  );

  return (
    <aside className="ticket">
      <h2>Tu pedido</h2>
      {lines.length === 0 ? <p className="muted">Agrega productos de la carta para empezar.</p> : (
        <form onSubmit={pedir}>
          <ul>
            {lines.map(({ p, n }) => (
              <li key={p.id}>
                <span>{p.nombre}</span>
                <span className="qty">
                  <button type="button" aria-label={`Quitar uno de ${p.nombre}`} onClick={() => cambiar(p.id, -1)}>−</button>
                  {n}
                  <button type="button" aria-label={`Agregar uno de ${p.nombre}`} onClick={() => cambiar(p.id, 1)}>+</button>
                </span>
                <span>{money(p.precio * n)}</span>
              </li>
            ))}
          </ul>
          <p className="total"><span>Total</span><b>{money(total)}</b></p>
          {user ? (
            <>
              <label>Dirección de entrega<input required value={dir} onChange={(e) => setDir(e.target.value)} placeholder="Calle 10 # 5-20" /></label>
              <label>Método de pago
                <select value={metodo} onChange={(e) => setMetodo(e.target.value)}>{METODOS.map((m) => <option key={m}>{m}</option>)}</select>
              </label>
              {error && <p className="error" role="alert">{error}</p>}
              <button className="primary" disabled={busy}>{busy ? 'Enviando…' : `Pedir por ${money(total)}`}</button>
            </>
          ) : (
            <button type="button" className="primary" onClick={goLogin}>Ingresa para pedir</button>
          )}
        </form>
      )}
    </aside>
  );
}
