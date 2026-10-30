import { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router';
import useApi from '../../hooks/useApi';
const links = [['/', 'Resumen general', '◫'], ['/estadisticas', 'Estadísticas', '▥'], ['/evaluaciones', 'Evaluaciones', '☷'], ['/grafo', 'Explorador de grafos', '◇']];

export default function AppShell() {
  const [open, setOpen] = useState(false);
  const health = useApi('/api/health/databases');
  const location = useLocation();
  const title = links.find(([path]) => path === location.pathname)?.[1] || 'Admisiones';
  return <div className="app-shell"><a className="skip-link" href="#content">Saltar al contenido</a>
    <aside className={`sidebar ${open ? 'is-open' : ''}`}>
      <NavLink to="/" className="brand" onClick={() => setOpen(false)}><span className="brand-mark">U</span><span>ADMISIONES<strong>USAC</strong></span></NavLink>
      <p className="nav-caption">PLATAFORMA DE ANÁLISIS</p>
      <nav aria-label="Navegación principal">{links.map(([to, text, icon]) => <NavLink key={to} to={to} end={to === '/'} onClick={() => setOpen(false)}><span className="nav-icon" aria-hidden="true">{icon}</span>{text}<span className="nav-arrow" aria-hidden="true">›</span></NavLink>)}</nav>
      <div className="sidebar-note"><span className="sidebar-note-icon">↗</span><strong>De los datos al conocimiento</strong><p>Pruebas específicas de admisión de Ingeniería.</p><span>2015 — 2024</span></div>
      <div className="sidebar-footer"><span className="small-dot"/>Proyecto académico · NoSQL<p>Ingeniería en Ciencias y Sistemas</p></div>
    </aside>
    {open && <button className="sidebar-overlay" aria-label="Cerrar navegación" onClick={() => setOpen(false)}/>}
    <div className="workspace"><header className="app-header"><div className="header-start"><button className="menu-toggle" onClick={() => setOpen(!open)} aria-expanded={open} aria-label="Abrir navegación">☰</button><span className="breadcrumb">Análisis de admisión <span>/</span> <strong>{title}</strong></span></div><div className="header-meta"><span className={`connection-pill ${health.status === 'success' ? 'online' : health.status === 'error' ? 'offline' : ''}`} role="status"><span className="small-dot"/>{health.status === 'success' ? 'Bases disponibles' : health.status === 'error' ? 'Servicio no disponible' : 'Conectando…'}</span><button className="icon-button" onClick={health.retry} aria-label="Comprobar conexión">↻</button><span className="profile-mark" aria-label="Proyecto USAC">US</span></div></header>
      <main id="content" tabIndex={-1}><Outlet/></main>
      <footer className="app-footer"><span>Universidad de San Carlos de Guatemala · Ingeniería</span><span>Datos abiertos · Proyecto de Bases de Datos NoSQL</span></footer>
    </div>
  </div>;
}
