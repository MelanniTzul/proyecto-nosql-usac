import { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router';
import useApi from '../../hooks/useApi';
const links = [['/', 'Resumen general', '◫'], ['/estadisticas', 'Estadísticas', '▥'], ['/evaluaciones', 'Evaluaciones', '☷'], ['/grafo', 'Explorador de grafos', '◇'], ['/consultas', 'Consultas NoSQL', '≡']];

export default function AppShell() {
  const [open, setOpen] = useState(false);
  const health = useApi('/api/health/databases');
  const [hasChecked, setHasChecked] = useState(false);
  const checking = health.status === 'loading';
  function checkStatus() {
    setHasChecked(true);
    health.retry();
  }
  const location = useLocation();
  const title = links.find(([path]) => path === location.pathname)?.[1] || 'Admisiones';
  return <div className="app-shell"><a className="skip-link" href="#content">Saltar al contenido</a>
    <aside className={`sidebar ${open ? 'is-open' : ''}`}>
      <NavLink to="/" className="brand" onClick={() => setOpen(false)}><img className="brand-mark" src="/escudo-usac.png" alt="Escudo de la USAC" width="44" height="44"/><span>ADMISIONES<strong>USAC</strong></span></NavLink>
      <p className="nav-caption">PLATAFORMA DE ANÁLISIS</p>
      <nav aria-label="Navegación principal">{links.map(([to, text, icon]) => <NavLink key={to} to={to} end={to === '/'} onClick={() => setOpen(false)}><span className="nav-icon" aria-hidden="true">{icon}</span>{text}<span className="nav-arrow" aria-hidden="true">›</span></NavLink>)}</nav>
      <div className="sidebar-note"><span className="sidebar-note-icon">↗</span><strong>De los datos al conocimiento</strong><p>Pruebas específicas de admisión de Ingeniería.</p><span>2015 — 2024</span></div>
    </aside>
    {open && <button className="sidebar-overlay" aria-label="Cerrar navegación" onClick={() => setOpen(false)}/>}
    <div className="workspace"><header className="app-header"><div className="header-start"><button className="menu-toggle" onClick={() => setOpen(!open)} aria-expanded={open} aria-label="Abrir navegación">☰</button><span className="breadcrumb">Análisis de admisión <span>/</span> <strong>{title}</strong></span></div><div className="header-meta"><span className={`connection-pill ${health.status === 'success' ? 'online' : health.status === 'error' ? 'offline' : ''}`} role="status"><span className="small-dot"/>{health.status === 'success' ? 'Sistema disponible' : health.status === 'error' ? 'Servicio no disponible' : 'Comprobando estado…'}</span><span className="status-action"><button className="icon-button status-check" onClick={checkStatus} disabled={checking} aria-busy={checking} aria-label="Comprobar conexión" aria-describedby="connection-status-help">{checking ? <span className="spinner" aria-hidden="true"/> : <span className="status-check-icon" aria-hidden="true">↻</span>}<span className="status-check-label">Comprobar conexión</span></button><span className="status-tooltip" id="connection-status-help" role="tooltip">Comprueba el estado de las conexiones. No actualiza los datos de las pantallas.</span></span>{hasChecked && !checking && <span className={`status-feedback ${health.status === 'error' ? 'has-error' : ''}`} role="status">{health.status === 'success' ? 'Estado actualizado' : 'No se pudo comprobar el estado. Intenta nuevamente.'}</span>}</div></header>
      <main id="content" tabIndex={-1}><Outlet/></main>
      <footer className="app-footer"><span>Universidad de San Carlos de Guatemala · Ingeniería</span></footer>
    </div>
  </div>;
}
